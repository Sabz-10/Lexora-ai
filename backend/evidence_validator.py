import re

from analysis_models import SourceEvidence

from document_models import (
    ParsedDocument,
    DocumentChunk,
)


# ============================================================
# NORMALIZATION WITH OFFSET MAPPING
# ============================================================

def normalize_with_offsets(text: str):

    normalized_chars = []
    offset_map = []

    for match in re.finditer(r"\s+|\S", text):

        value = match.group()

        if value.isspace():

            normalized_chars.append(" ")

        else:

            normalized_chars.append(value)

        offset_map.append(
            (match.start(), match.end())
        )

    return "".join(normalized_chars), offset_map


# ============================================================
# SOURCE EVIDENCE VERIFICATION
# ============================================================

def find_source_evidence(
    excerpt: str,
    chunk: DocumentChunk,
    document: ParsedDocument,
) -> list[SourceEvidence]:

    excerpt = excerpt.strip()

    if not excerpt:
        return []

    full_text = document.full_text

    # Validate chunk coordinates.
    if not (
        0 <= chunk.start_offset
        < chunk.end_offset
        <= len(full_text)
    ):
        raise ValueError(
            "Invalid chunk offsets."
        )

    # Verify original chunk content.
    if (
        full_text[
            chunk.start_offset:chunk.end_offset
        ] != chunk.text
    ):
        raise ValueError(
            "Chunk does not match the original document."
        )

    # Normalize whitespace in both strings.
    normalized_chunk, offset_map = (
        normalize_with_offsets(chunk.text)
    )

    normalized_excerpt, _ = (
        normalize_with_offsets(excerpt)
    )

    evidence_list = []

    search_start = 0

    while True:

        normalized_start = normalized_chunk.find(
            normalized_excerpt,
            search_start,
        )

        if normalized_start == -1:
            break

        normalized_end = (
            normalized_start
            + len(normalized_excerpt)
        )

        # Recover original chunk coordinates.
        local_start = offset_map[
            normalized_start
        ][0]

        local_end = offset_map[
            normalized_end - 1
        ][1]

        # Convert to global document coordinates.
        global_start = (
            chunk.start_offset + local_start
        )

        global_end = (
            chunk.start_offset + local_end
        )

        # Recover the actual original excerpt.
        original_excerpt = full_text[
            global_start:global_end
        ]

        source_block_ids = [
            block.block_id
            for block in document.blocks
            if (
                block.start_offset < global_end
                and block.end_offset > global_start
            )
        ]

        if not source_block_ids:

            raise ValueError(
                "Evidence could not be mapped "
                "to source blocks."
            )

        evidence = SourceEvidence(
            excerpt=original_excerpt,
            chunk_id=chunk.chunk_id,
            start_offset=global_start,
            end_offset=global_end,
            source_block_ids=source_block_ids,
        )

        evidence_list.append(evidence)

        search_start = normalized_start + 1

    return evidence_list