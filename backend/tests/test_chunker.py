import pytest

from chunker import chunk_document
from document_models import DocumentBlock, ParsedDocument
from token_utils import estimate_tokens


def create_document(texts):
    blocks = []
    offset = 0

    for i, text in enumerate(texts, start=1):
        blocks.append(
            DocumentBlock(
                block_id=i,
                text=text,
                source_type="paragraph",
                source_number=i,
                start_offset=offset,
                end_offset=offset + len(text),
            )
        )

        offset += len(text) + 1

    return ParsedDocument(
        filename="sample.txt",
        file_type=".txt",
        blocks=blocks,
        total_characters=len("\n".join(texts)),
    )


def test_single_chunk():
    document = create_document(
        ["This is a rental agreement."]
    )

    chunks = chunk_document(document)

    assert len(chunks) == 1
    assert chunks[0].text == document.full_text


def test_multiple_chunks():
    document = create_document(["word " * 1000])

    chunks = chunk_document(
        document,
        target_tokens=100,
        overlap_tokens=10,
    )

    assert len(chunks) > 1


def test_source_offsets():
    document = create_document(["Contract terms " * 500])

    chunks = chunk_document(
        document,
        target_tokens=100,
        overlap_tokens=10,
    )

    for chunk in chunks:
        assert chunk.text == document.full_text[
            chunk.start_offset:chunk.end_offset
        ]


def test_token_budget():
    document = create_document(["Agreement " * 1000])

    chunks = chunk_document(
        document,
        target_tokens=100,
        overlap_tokens=10,
    )

    for chunk in chunks:
        assert chunk.estimated_tokens <= 100
        assert chunk.estimated_tokens == estimate_tokens(
            chunk.text
        )


def test_complete_coverage():
    document = create_document(["Legal agreement " * 500])

    chunks = chunk_document(
        document,
        target_tokens=100,
        overlap_tokens=10,
    )

    covered = set()

    for chunk in chunks:
        covered.update(
            range(chunk.start_offset, chunk.end_offset)
        )

    assert covered == set(
        range(len(document.full_text))
    )


def test_chunk_overlap():
    document = create_document(["Contract " * 500])

    chunks = chunk_document(
        document,
        target_tokens=100,
        overlap_tokens=10,
    )

    for previous, current in zip(chunks, chunks[1:]):
        assert previous.end_offset - current.start_offset == 40

        assert previous.text[-40:] == current.text[:40]


def test_source_block_mapping():
    document = create_document([
        "First clause.",
        "Second clause.",
        "Third clause.",
    ])

    chunks = chunk_document(document)

    assert chunks[0].source_block_ids == [1, 2, 3]


def test_invalid_overlap():
    document = create_document(["Sample contract"])

    with pytest.raises(ValueError):
        chunk_document(
            document,
            target_tokens=100,
            overlap_tokens=100,
        )
def test_empty_document():
    document = create_document([])

    assert chunk_document(document) == []


def test_invalid_target():
    document = create_document(["Agreement"])

    with pytest.raises(ValueError):
        chunk_document(
            document,
            target_tokens=0,
            overlap_tokens=0,
        )


def test_zero_overlap():
    document = create_document(["Contract " * 100])

    chunks = chunk_document(
        document,
        target_tokens=20,
        overlap_tokens=0,
    )

    assert len(chunks) > 1

    for previous, current in zip(chunks, chunks[1:]):
        assert previous.end_offset == current.start_offset


def test_hard_split():
    document = create_document(["A" * 1000])

    chunks = chunk_document(
        document,
        target_tokens=20,
        overlap_tokens=0,
    )

    assert "".join(chunk.text for chunk in chunks) == (
        document.full_text
    )


def test_clause_boundary():
    document = create_document([
        "A" * 59 + "\nClause 2. Payment " + "B" * 100
    ])

    chunks = chunk_document(
        document,
        target_tokens=20,
        overlap_tokens=0,
    )

    assert chunks[0].end_offset == 60
    assert chunks[1].text.startswith("Clause 2.")