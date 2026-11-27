import pytest

from pydantic import ValidationError

from analysis_models import SourceEvidence

from document_models import (
    DocumentBlock,
    ParsedDocument,
    DocumentChunk,
)

from evidence_validator import find_source_evidence


# ============================================================
# TEST HELPERS
# ============================================================

def create_document(texts):

    blocks = []
    offset = 0

    for index, text in enumerate(texts, start=1):

        block = DocumentBlock(
            block_id=index,
            text=text,
            source_type="page",
            source_number=index,
            start_offset=offset,
            end_offset=offset + len(text),
        )

        blocks.append(block)

        offset += len(text) + 1

    return ParsedDocument(
        filename="sample.pdf",
        file_type="pdf",
        blocks=blocks,
        total_characters=len("\n".join(texts)),
    )


def create_chunk(document, start=0, end=None):

    full_text = document.full_text

    if end is None:
        end = len(full_text)

    text = full_text[start:end]

    return DocumentChunk(
        chunk_id=1,
        text=text,
        start_offset=start,
        end_offset=end,
        estimated_tokens=(len(text) + 3) // 4,
        source_block_ids=[
            block.block_id
            for block in document.blocks
            if (
                block.start_offset < end
                and block.end_offset > start
            )
        ],
    )


# ============================================================
# EXACT EVIDENCE MATCHING
# ============================================================

def test_exact_match():

    document = create_document([
        "The tenant must pay monthly rent."
    ])

    chunk = create_chunk(document)

    results = find_source_evidence(
        "monthly rent",
        chunk,
        document,
    )

    assert len(results) == 1

    assert results[0].excerpt == "monthly rent"
    assert results[0].source_block_ids == [1]
    assert results[0].chunk_id == 1


def test_fabricated_excerpt():

    document = create_document([
        "Monthly rent is Rs. 5000."
    ])

    chunk = create_chunk(document)

    results = find_source_evidence(
        "Monthly rent is Rs. 9000.",
        chunk,
        document,
    )

    assert results == []


@pytest.mark.parametrize("excerpt", ["", "   "])
def test_empty_excerpt(excerpt):

    document = create_document(["Sample contract."])

    chunk = create_chunk(document)

    assert find_source_evidence(
        excerpt,
        chunk,
        document,
    ) == []


# ============================================================
# OFFSET VERIFICATION
# ============================================================

def test_exact_offsets():

    document = create_document([
        "Rent: 5000. Fee: 500."
    ])

    chunk = create_chunk(document)

    evidence = find_source_evidence(
        "Fee: 500.",
        chunk,
        document,
    )[0]

    assert evidence.start_offset == 12
    assert evidence.end_offset == 21

    assert document.full_text[
        evidence.start_offset:evidence.end_offset
    ] == evidence.excerpt


def test_nonzero_chunk_offset():

    document = create_document([
        "Introduction.\nLate fee is Rs. 500."
    ])

    start = document.full_text.index("Late")

    chunk = create_chunk(document, start=start)

    evidence = find_source_evidence(
        "Late fee",
        chunk,
        document,
    )[0]

    assert evidence.start_offset == start
    assert evidence.end_offset == start + 8


# ============================================================
# SOURCE BLOCK MAPPING
# ============================================================

def test_second_source_block():

    document = create_document([
        "Monthly rent is Rs. 5000.",
        "Late fee is Rs. 500.",
    ])

    chunk = create_chunk(document)

    evidence = find_source_evidence(
        "Late fee is Rs. 500.",
        chunk,
        document,
    )[0]

    assert evidence.source_block_ids == [2]


def test_cross_block_evidence():

    document = create_document([
        "Payment is due",
        "within 30 days.",
    ])

    chunk = create_chunk(document)

    evidence = find_source_evidence(
        "Payment is due\nwithin 30 days.",
        chunk,
        document,
    )[0]

    assert evidence.source_block_ids == [1, 2]

    assert evidence.start_offset == 0
    assert evidence.end_offset == len(document.full_text)


# ============================================================
# REPEATED EVIDENCE
# ============================================================

def test_repeated_excerpt():

    document = create_document([
        "Payment required.",
        "Payment required.",
    ])

    chunk = create_chunk(document)

    results = find_source_evidence(
        "Payment required.",
        chunk,
        document,
    )

    assert len(results) == 2

    assert results[0].source_block_ids == [1]
    assert results[1].source_block_ids == [2]

    assert (
        results[0].start_offset
        != results[1].start_offset
    )


def test_excerpt_outside_chunk():

    document = create_document([
        "Monthly rent is Rs. 5000.",
        "Late fee is Rs. 500.",
    ])

    chunk = create_chunk(
        document,
        end=document.blocks[0].end_offset,
    )

    results = find_source_evidence(
        "Late fee is Rs. 500.",
        chunk,
        document,
    )

    assert results == []


# ============================================================
# CHUNK INTEGRITY
# ============================================================

def test_invalid_chunk_offsets():

    document = create_document([
        "Sample contract."
    ])

    chunk = create_chunk(document)

    chunk.start_offset = -1

    with pytest.raises(ValueError):
        find_source_evidence(
            "Sample",
            chunk,
            document,
        )


def test_chunk_content_mismatch():

    document = create_document([
        "Sample contract."
    ])

    chunk = create_chunk(document)

    chunk.text = "Modified contract."

    with pytest.raises(ValueError):
        find_source_evidence(
            "Modified",
            chunk,
            document,
        )


# ============================================================
# UNICODE AND MATCHING BEHAVIOUR
# ============================================================

def test_unicode_evidence():

    document = create_document([
        "மாத வாடகை ₹5000"
    ])

    chunk = create_chunk(document)

    evidence = find_source_evidence(
        "₹5000",
        chunk,
        document,
    )[0]

    assert document.full_text[
        evidence.start_offset:evidence.end_offset
    ] == "₹5000"


def test_case_sensitive_matching():

    document = create_document([
        "Monthly Rent"
    ])

    chunk = create_chunk(document)

    assert find_source_evidence(
        "monthly rent",
        chunk,
        document,
    ) == []


# ============================================================
# EVIDENCE MODEL VALIDATION
# ============================================================

def test_invalid_evidence_range():

    with pytest.raises(ValidationError):

        SourceEvidence(
            excerpt="Payment",
            chunk_id=1,
            start_offset=10,
            end_offset=5,
            source_block_ids=[1],
        )


def test_missing_source_blocks():

    with pytest.raises(ValidationError):

        SourceEvidence(
            excerpt="Payment",
            chunk_id=1,
            start_offset=0,
            end_offset=7,
            source_block_ids=[],
        )
def test_newline_normalization():

    document = create_document([
        "The tenant must pay\nmonthly rent."
    ])

    chunk = create_chunk(document)

    results = find_source_evidence(
        "The tenant must pay monthly rent.",
        chunk,
        document,
    )

    assert len(results) == 1

    assert results[0].excerpt == (
        "The tenant must pay\nmonthly rent."
    )


def test_multiple_space_normalization():

    document = create_document([
        "Monthly rent is    Rs. 5000."
    ])

    chunk = create_chunk(document)

    results = find_source_evidence(
        "Monthly rent is Rs. 5000.",
        chunk,
        document,
    )

    assert len(results) == 1


def test_normalized_offset_integrity():

    document = create_document([
        "Introduction.\nPayment is\t\t due."
    ])

    chunk = create_chunk(document)

    evidence = find_source_evidence(
        "Payment is due.",
        chunk,
        document,
    )[0]

    assert document.full_text[
        evidence.start_offset:evidence.end_offset
    ] == evidence.excerpt

    assert evidence.excerpt == "Payment is\t\t due."


def test_normalization_rejects_changed_amount():

    document = create_document([
        "Monthly rent is\nRs. 5000."
    ])

    chunk = create_chunk(document)

    results = find_source_evidence(
        "Monthly rent is Rs. 9000.",
        chunk,
        document,
    )

    assert results == []