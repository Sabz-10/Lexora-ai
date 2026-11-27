import logging
from retry_handler import execute_with_retry

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from config import MAX_CONCURRENT_REQUESTS

from analysis_models import DocumentAnalysisResult

from document_models import ParsedDocument

from analysis_router import create_analysis_plan

from chunk_analyzer import (
    analyze_chunk,
    AIProvider,
)


logger = logging.getLogger(__name__)
# ============================================================
# RETRY-ENABLED CHUNK EXECUTION
# ============================================================

def analyze_chunk_with_retry(
    chunk,
    document,
    provider,
    doc_type,
):

    return execute_with_retry(
        lambda: analyze_chunk(
            chunk=chunk,
            document=document,
            provider=provider,
            doc_type=doc_type,
        )
    )


# ============================================================
# DOCUMENT ANALYSIS ORCHESTRATOR
# ============================================================

def analyze_document(
    document: ParsedDocument,
    provider: AIProvider,
    doc_type: str = "other",
    max_workers: int = MAX_CONCURRENT_REQUESTS,
) -> DocumentAnalysisResult:

    if max_workers < 1:

        raise ValueError(
            "max_workers must be at least 1."
        )

    # --------------------------------------------------------
    # STEP 1: CREATE ANALYSIS PLAN
    # --------------------------------------------------------

    plan = create_analysis_plan(document)

    logger.info(
        "Document analysis started: strategy=%s "
        "chunks=%s estimated_tokens=%s",
        plan.strategy,
        plan.total_chunks,
        plan.total_estimated_tokens,
    )

    chunk_results = []

    # --------------------------------------------------------
    # STEP 2: SEQUENTIAL EXECUTION
    # --------------------------------------------------------

    if plan.total_chunks == 1 or max_workers == 1:

        for chunk in plan.chunks:

            result = analyze_chunk_with_retry(
    chunk=chunk,
    document=document,
    provider=provider,
    doc_type=doc_type,
)

            chunk_results.append(result)

    # --------------------------------------------------------
    # STEP 3: CONCURRENT EXECUTION
    # --------------------------------------------------------

    else:

        worker_count = min(
            max_workers,
            plan.total_chunks,
        )

        with ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:

            future_to_chunk = {}

            for chunk in plan.chunks:

                future = executor.submit(
    analyze_chunk_with_retry,
    chunk,
    document,
    provider,
    doc_type,
)

                future_to_chunk[future] = chunk.chunk_id

            try:

                for future in as_completed(
                    future_to_chunk
                ):

                    chunk_id = future_to_chunk[future]

                    result = future.result()

                    chunk_results.append(result)

                    logger.info(
                        "Chunk %s completed.",
                        chunk_id,
                    )

            except Exception:

                # Cancel tasks that have not started.
                for future in future_to_chunk:

                    future.cancel()

                raise

    # --------------------------------------------------------
    # STEP 4: RESTORE ORIGINAL DOCUMENT ORDER
    # --------------------------------------------------------

    chunk_results.sort(
        key=lambda result: result.chunk_id
    )

    # --------------------------------------------------------
    # STEP 5: BUILD DOCUMENT RESULT
    # --------------------------------------------------------

    document_result = DocumentAnalysisResult(
        strategy=plan.strategy,
        total_estimated_tokens=(
            plan.total_estimated_tokens
        ),
        total_chunks=plan.total_chunks,
        chunk_results=chunk_results,
    )

    logger.info(
        "Document analysis completed: "
        "chunks=%s clauses=%s facts=%s",
        document_result.completed_chunks,
        document_result.total_clauses,
        document_result.total_key_facts,
    )

    return document_result