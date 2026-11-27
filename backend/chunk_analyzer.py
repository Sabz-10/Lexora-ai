from collections.abc import Callable

from analysis_models import (
    ChunkAnalysisResponse,
    VerifiedClauseFinding,
    VerifiedKeyFact,
    VerifiedChunkResult,
)

from document_models import (
    ParsedDocument,
    DocumentChunk,
)

from prompt_builder import (
    build_chunk_prompt,
    CHUNK_SYSTEM_INSTRUCTIONS,
)

from evidence_validator import find_source_evidence


# ============================================================
# AI PROVIDER INTERFACE
# ============================================================

AIProvider = Callable[[str, str], dict]


# ============================================================
# CUSTOM EXCEPTION
# ============================================================

class EvidenceValidationError(ValueError):
    pass


# ============================================================
# CHUNK ANALYSIS
# ============================================================

def analyze_chunk(
    chunk: DocumentChunk,
    document: ParsedDocument,
    provider: AIProvider,
    doc_type: str = "other",
) -> VerifiedChunkResult:

    # --------------------------------------------------------
    # STEP 1: Verify chunk integrity
    # --------------------------------------------------------

    full_text = document.full_text

    if not (
        0 <= chunk.start_offset
        < chunk.end_offset
        <= len(full_text)
    ):
        raise ValueError("Invalid chunk offsets.")

    if (
        full_text[
            chunk.start_offset:chunk.end_offset
        ] != chunk.text
    ):
        raise ValueError(
            "Chunk does not match the original document."
        )

    # --------------------------------------------------------
    # STEP 2: Construct prompt
    # --------------------------------------------------------

    prompt = build_chunk_prompt(
        chunk,
        doc_type,
    )

    # --------------------------------------------------------
    # STEP 3: Execute AI provider
    # --------------------------------------------------------

    raw_response = provider(
        CHUNK_SYSTEM_INSTRUCTIONS,
        prompt,
    )

    # --------------------------------------------------------
    # STEP 4: Validate AI response structure
    # --------------------------------------------------------

    response = ChunkAnalysisResponse.model_validate(
        raw_response
    )

    verified_clauses = []
    verified_facts = []

    # --------------------------------------------------------
    # STEP 5: Verify clause evidence
    # --------------------------------------------------------

    for index, clause in enumerate(
        response.clauses,
        start=1,
    ):

        evidence = find_source_evidence(
            clause.text,
            chunk,
            document,
        )

        if not evidence:
            raise EvidenceValidationError(
                f"Clause {index} in chunk "
                f"{chunk.chunk_id} has no valid evidence."
            )

        verified_clauses.append(
            VerifiedClauseFinding(
                finding=clause,
                evidence=evidence,
            )
        )

    # --------------------------------------------------------
    # STEP 6: Verify key fact evidence
    # --------------------------------------------------------

    for index, fact in enumerate(
        response.key_facts,
        start=1,
    ):

        evidence = find_source_evidence(
            fact.source_excerpt,
            chunk,
            document,
        )

        if not evidence:
            raise EvidenceValidationError(
                f"Key fact {index} in chunk "
                f"{chunk.chunk_id} has no valid evidence."
            )

        verified_facts.append(
            VerifiedKeyFact(
                fact=fact,
                evidence=evidence,
            )
        )

    # --------------------------------------------------------
    # STEP 7: Return verified chunk result
    # --------------------------------------------------------

    return VerifiedChunkResult(
        chunk_id=chunk.chunk_id,
        clauses=verified_clauses,
        key_facts=verified_facts,
    )