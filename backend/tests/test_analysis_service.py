import json

from unittest.mock import Mock

import pytest
from google.genai import errors
from pydantic import ValidationError

from config import SINGLE_PASS_MAX_TOKENS

from document_models import (
    DocumentBlock,
    ParsedDocument,
)

from analysis_models import AnalysisExecutionResult

from analysis_service import execute_document_analysis

from gemini_provider import GeminiConfigurationError

from request_budget import RequestBudgetExceededError

from retry_handler import RetryExhaustedError


# ============================================================
# TEST CONFIGURATION
# ============================================================

MODELS = ["model-primary", "model-fallback"]


@pytest.fixture(autouse=True)
def disable_retry_waiting(monkeypatch):

    monkeypatch.setattr(
        "retry_handler.time.sleep",
        Mock(),
    )


# ============================================================
# TEST HELPERS
# ============================================================

def create_document(text="Monthly rent is Rs. 5000."):

    block = DocumentBlock(
        block_id=1,
        text=text,
        source_type="text",
        source_number=1,
        start_offset=0,
        end_offset=len(text),
    )

    return ParsedDocument(
        filename="sample.txt",
        file_type="txt",
        blocks=[block],
        total_characters=len(text),
    )


def create_large_document():

    return create_document(
        "A" * (SINGLE_PASS_MAX_TOKENS * 4 + 1)
    )


def mock_response():

    response = Mock()

    response.text = json.dumps({
        "clauses": [],
        "key_facts": [],
    })

    return response


def create_client():

    client = Mock()

    client.models.generate_content.return_value = (
        mock_response()
    )

    return client


def create_api_error(status_code):

    error_class = (
        errors.ClientError
        if status_code < 500
        else errors.ServerError
    )

    return error_class(
        status_code,
        {
            "error": {
                "code": status_code,
                "message": "Simulated API failure",
            }
        },
    )


# ============================================================
# SUCCESSFUL DOCUMENT ANALYSIS
# ============================================================

def test_single_pass_execution():

    client = create_client()

    result = execute_document_analysis(
        document=create_document(),
        client=client,
        models=MODELS,
    )

    assert isinstance(
        result,
        AnalysisExecutionResult,
    )

    assert result.analysis.strategy == "single_pass"
    assert result.analysis.completed_chunks == 1
    assert result.requests_used == 1


def test_multi_chunk_execution():

    client = create_client()

    result = execute_document_analysis(
        document=create_large_document(),
        client=client,
        models=MODELS,
        max_workers=2,
    )

    assert result.analysis.strategy == "multi_chunk"

    assert result.analysis.total_chunks > 1

    assert (
        result.analysis.completed_chunks
        == result.analysis.total_chunks
    )

    assert (
        result.requests_used
        == result.analysis.total_chunks
    )

    assert (
        client.models.generate_content.call_count
        == result.requests_used
    )


# ============================================================
# RESOURCE USAGE
# ============================================================

def test_request_usage_metadata():

    client = create_client()

    result = execute_document_analysis(
        document=create_document(),
        client=client,
        models=MODELS,
        max_requests=10,
    )

    assert result.requests_used == 1
    assert result.request_limit == 10
    assert result.requests_remaining == 9


def test_independent_document_budgets():

    client = create_client()

    first_result = execute_document_analysis(
        document=create_document(),
        client=client,
        models=MODELS,
        max_requests=1,
    )

    second_result = execute_document_analysis(
        document=create_document(),
        client=client,
        models=MODELS,
        max_requests=1,
    )

    assert first_result.requests_used == 1
    assert second_result.requests_used == 1

    assert (
        client.models.generate_content.call_count
        == 2
    )


# ============================================================
# MODEL FALLBACK
# ============================================================

def test_fallback_request_accounting():

    client = create_client()

    client.models.generate_content.side_effect = [
        create_api_error(503),
        mock_response(),
    ]

    result = execute_document_analysis(
        document=create_document(),
        client=client,
        models=MODELS,
        max_requests=5,
    )

    assert result.requests_used == 2
    assert result.requests_remaining == 3


# ============================================================
# RETRY RECOVERY
# ============================================================

def test_retry_recovery_request_accounting():

    client = create_client()

    client.models.generate_content.side_effect = [
        create_api_error(503),
        create_api_error(503),
        mock_response(),
    ]

    result = execute_document_analysis(
        document=create_document(),
        client=client,
        models=MODELS,
        max_requests=10,
    )

    assert result.requests_used == 3

    assert result.analysis.completed_chunks == 1


def test_retry_exhaustion():

    client = create_client()

    client.models.generate_content.side_effect = (
        create_api_error(503)
    )

    with pytest.raises(RetryExhaustedError):

        execute_document_analysis(
            document=create_document(),
            client=client,
            models=MODELS,
            max_requests=20,
        )

    assert (
        client.models.generate_content.call_count
        == 6
    )


# ============================================================
# BUDGET EXHAUSTION
# ============================================================

def test_budget_exhaustion_prevents_retry():

    client = create_client()

    client.models.generate_content.side_effect = (
        create_api_error(503)
    )

    with pytest.raises(RequestBudgetExceededError):

        execute_document_analysis(
            document=create_document(),
            client=client,
            models=MODELS,
            max_requests=2,
        )

    assert (
        client.models.generate_content.call_count
        == 2
    )


def test_concurrent_budget_exhaustion():

    client = create_client()

    with pytest.raises(RequestBudgetExceededError):

        execute_document_analysis(
            document=create_large_document(),
            client=client,
            models=MODELS,
            max_requests=2,
            max_workers=2,
        )

    assert (
        client.models.generate_content.call_count
        == 2
    )


# ============================================================
# NON-RETRYABLE FAILURES
# ============================================================

def test_configuration_error_terminates():

    client = create_client()

    client.models.generate_content.side_effect = (
        create_api_error(401)
    )

    with pytest.raises(GeminiConfigurationError):

        execute_document_analysis(
            document=create_document(),
            client=client,
            models=MODELS,
        )

    assert (
        client.models.generate_content.call_count
        == 1
    )


def test_empty_document_prevents_api_request():

    client = create_client()

    with pytest.raises(ValueError):

        execute_document_analysis(
            document=create_document(""),
            client=client,
            models=MODELS,
        )

    client.models.generate_content.assert_not_called()


# ============================================================
# EXECUTION RESULT VALIDATION
# ============================================================

def test_invalid_request_usage_rejected():

    client = create_client()

    result = execute_document_analysis(
        document=create_document(),
        client=client,
        models=MODELS,
    )

    with pytest.raises(ValidationError):

        AnalysisExecutionResult(
            analysis=result.analysis,
            requests_used=11,
            request_limit=10,
        )