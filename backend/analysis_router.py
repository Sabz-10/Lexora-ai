from config import SINGLE_PASS_MAX_TOKENS

from document_models import (
    ParsedDocument,
    DocumentChunk,
    AnalysisPlan,
)

from token_utils import estimate_tokens
from chunker import chunk_document


def create_analysis_plan(
    document: ParsedDocument,
) -> AnalysisPlan:

    text = document.full_text

    if not text.strip():
        raise ValueError("Document contains no readable text.")

    total_tokens = estimate_tokens(text)

    if total_tokens <= SINGLE_PASS_MAX_TOKENS:

        chunk = DocumentChunk(
            chunk_id=1,
            text=text,
            start_offset=0,
            end_offset=len(text),
            estimated_tokens=total_tokens,
            source_block_ids=[
                block.block_id
                for block in document.blocks
            ],
        )

        return AnalysisPlan(
            strategy="single_pass",
            total_estimated_tokens=total_tokens,
            chunks=[chunk],
        )

    chunks = chunk_document(document)

    return AnalysisPlan(
        strategy="multi_chunk",
        total_estimated_tokens=total_tokens,
        chunks=chunks,
    )