import logging

from config import (
    MAX_API_REQUESTS_PER_DOCUMENT,
    MAX_CONCURRENT_REQUESTS,
)

from document_models import ParsedDocument

from analysis_models import AnalysisExecutionResult

from request_budget import RequestBudget

from gemini_provider import GeminiProvider

from analysis_orchestrator import analyze_document


logger = logging.getLogger(__name__)


# ============================================================
# DOCUMENT ANALYSIS SERVICE
# ============================================================

def execute_document_analysis(
    document: ParsedDocument,
    client,
    models,
    doc_type: str = "other",
    max_requests: int = MAX_API_REQUESTS_PER_DOCUMENT,
    max_workers: int = MAX_CONCURRENT_REQUESTS,
) -> AnalysisExecutionResult:

    # --------------------------------------------------------
    # STEP 1: CREATE A DOCUMENT-SPECIFIC REQUEST BUDGET
    # --------------------------------------------------------

    budget = RequestBudget(
        max_requests=max_requests,
    )

    # --------------------------------------------------------
    # STEP 2: CREATE A BUDGET-AWARE AI PROVIDER
    # --------------------------------------------------------

    provider = GeminiProvider(
        client=client,
        models=models,
        request_budget=budget,
    )

    try:

        # ----------------------------------------------------
        # STEP 3: EXECUTE DOCUMENT ANALYSIS
        # ----------------------------------------------------

        analysis = analyze_document(
            document=document,
            provider=provider,
            doc_type=doc_type,
            max_workers=max_workers,
        )

        # ----------------------------------------------------
        # STEP 4: RETURN ANALYSIS AND RESOURCE USAGE
        # ----------------------------------------------------

        return AnalysisExecutionResult(
            analysis=analysis,
            requests_used=budget.used_requests,
            request_limit=budget.max_requests,
        )

    finally:

        # ----------------------------------------------------
        # RECORD RESOURCE USAGE EVEN IF ANALYSIS FAILS
        # ----------------------------------------------------

        logger.info(
            "Document request usage: used=%s limit=%s "
            "remaining=%s",
            budget.used_requests,
            budget.max_requests,
            budget.remaining_requests,
        )