import re

from config import (
    CHUNK_TARGET_TOKENS,
    CHUNK_OVERLAP_TOKENS,
)

from document_models import (
    ParsedDocument,
    DocumentChunk,
)

from token_utils import estimate_tokens


def chunk_document(
    document: ParsedDocument,
    target_tokens: int = CHUNK_TARGET_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
) -> list[DocumentChunk]:

    if target_tokens <= 0:
        raise ValueError("Target tokens must be positive.")

    if not 0 <= overlap_tokens < target_tokens:
        raise ValueError("Invalid chunk overlap.")

    text = document.full_text

    if not text:
        return []

    max_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4

    boundaries = {
        block.start_offset
        for block in document.blocks
    }

    for match in re.finditer(
        r"(?im)^[ \t]*(?:(?:clause|section|article)\s+\d+|\d+[.)])",
        text,
    ):
        boundaries.add(match.start())

    boundaries = sorted(boundaries)

    chunks = []
    start = 0

    while start < len(text):

        end = min(start + max_chars, len(text))

        if end < len(text):

            min_end = start + max(
                max_chars // 2,
                overlap_chars + 1,
            )

            candidates = [
                boundary
                for boundary in boundaries
                if min_end <= boundary <= end
            ]

            if candidates:
                end = candidates[-1]

            else:
                whitespace = text.rfind(
                    " ", min_end, end
                )

                if whitespace != -1:
                    end = whitespace + 1

        chunk_text = text[start:end]

        source_block_ids = [
            block.block_id
            for block in document.blocks
            if block.start_offset < end
            and block.end_offset > start
        ]

        chunks.append(
            DocumentChunk(
                chunk_id=len(chunks) + 1,
                text=chunk_text,
                start_offset=start,
                end_offset=end,
                estimated_tokens=estimate_tokens(
                    chunk_text
                ),
                source_block_ids=source_block_ids,
            )
        )

        if end == len(text):
            break

        start = end - overlap_chars

    return chunks