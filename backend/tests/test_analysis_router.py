import pytest

from analysis_router import create_analysis_plan
from config import SINGLE_PASS_MAX_TOKENS
from document_models import DocumentBlock, ParsedDocument


def create_document(text):
    return ParsedDocument(
        filename="sample.txt",
        file_type=".txt",
        blocks=[
            DocumentBlock(
                block_id=1,
                text=text,
                source_type="paragraph",
                source_number=1,
                start_offset=0,
                end_offset=len(text),
            )
        ],
        total_characters=len(text),
    )


def test_single_pass():
    document = create_document("Sample rental agreement.")

    plan = create_analysis_plan(document)

    assert plan.strategy == "single_pass"
    assert plan.total_chunks == 1
    assert plan.chunks[0].text == document.full_text


def test_multi_chunk():
    document = create_document(
        "A" * (SINGLE_PASS_MAX_TOKENS * 4 + 1)
    )

    plan = create_analysis_plan(document)

    assert plan.strategy == "multi_chunk"
    assert plan.total_chunks > 1


def test_below_threshold():
    document = create_document(
        "A" * ((SINGLE_PASS_MAX_TOKENS - 1) * 4)
    )

    plan = create_analysis_plan(document)

    assert plan.strategy == "single_pass"


def test_exact_threshold():
    document = create_document(
        "A" * (SINGLE_PASS_MAX_TOKENS * 4)
    )

    plan = create_analysis_plan(document)

    assert plan.strategy == "single_pass"
    assert plan.total_estimated_tokens == SINGLE_PASS_MAX_TOKENS


def test_above_threshold():
    document = create_document(
        "A" * (SINGLE_PASS_MAX_TOKENS * 4 + 1)
    )

    plan = create_analysis_plan(document)

    assert plan.strategy == "multi_chunk"
    assert plan.total_estimated_tokens == (
        SINGLE_PASS_MAX_TOKENS + 1
    )


def test_empty_document():
    document = create_document("")

    with pytest.raises(ValueError):
        create_analysis_plan(document)


def test_whitespace_document():
    document = create_document("   \n\t   ")

    with pytest.raises(ValueError):
        create_analysis_plan(document)


def test_single_pass_source_mapping():
    document = create_document("Sample agreement")

    plan = create_analysis_plan(document)

    chunk = plan.chunks[0]

    assert chunk.start_offset == 0
    assert chunk.end_offset == len(document.full_text)
    assert chunk.source_block_ids == [1]