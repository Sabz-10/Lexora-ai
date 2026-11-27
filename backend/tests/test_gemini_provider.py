from config import GEMINI_REQUEST_TIMEOUT_MS

from request_budget import (
    RequestBudget,
    RequestBudgetExceededError,
)
import httpx
import json
from unittest.mock import Mock

import pytest
from google.genai import errors

from analysis_models import ChunkAnalysisResponse

from gemini_provider import (
    GeminiProvider,
    GeminiConfigurationError,
    GeminiUnavailableError,
    GeminiInvalidResponseError,
    GeminiProviderError,
)


# ============================================================
# TEST HELPERS
# ============================================================

MODELS = ["model-primary", "model-fallback"]


def valid_response():

    return {
        "clauses": [],
        "key_facts": [
            {
                "label": "Monthly rent",
                "value": "Rs. 5000",
                "source_excerpt":
                    "Monthly rent is Rs. 5000.",
            }
        ],
    }


def mock_response(data):

    response = Mock()

    response.text = json.dumps(data)

    return response


def create_provider():

    client = Mock()

    provider = GeminiProvider(
        client,
        MODELS,
    )

    return client, provider


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
# CONFIGURATION VALIDATION
# ============================================================

def test_missing_client():

    with pytest.raises(GeminiConfigurationError):

        GeminiProvider(None, MODELS)


def test_missing_models():

    with pytest.raises(GeminiConfigurationError):

        GeminiProvider(Mock(), [])


# ============================================================
# SUCCESSFUL PROVIDER EXECUTION
# ============================================================

def test_successful_response():

    client, provider = create_provider()

    client.models.generate_content.return_value = (
        mock_response(valid_response())
    )

    result = provider(
        "System instructions",
        "Contract prompt",
    )

    assert result == valid_response()

    assert (
        client.models.generate_content.call_count
        == 1
    )


def test_correct_model_selected():

    client, provider = create_provider()

    client.models.generate_content.return_value = (
        mock_response(valid_response())
    )

    provider("System instructions", "Contract prompt")

    request = (
        client.models.generate_content.call_args.kwargs
    )

    assert request["model"] == "model-primary"

    assert request["contents"] == "Contract prompt"


def test_structured_output_configuration():

    client, provider = create_provider()

    client.models.generate_content.return_value = (
        mock_response(valid_response())
    )

    provider("System instructions", "Contract prompt")

    request = (
        client.models.generate_content.call_args.kwargs
    )

    config = request["config"]

    assert (
        config.system_instruction
        == "System instructions"
    )

    assert (
        config.response_mime_type
        == "application/json"
    )

    assert (
        config.response_json_schema
        == ChunkAnalysisResponse.model_json_schema()
    )


# ============================================================
# MODEL FALLBACK
# ============================================================

@pytest.mark.parametrize(
    "status_code",
    [404, 408, 429, 500, 502, 503, 504],
)
def test_api_failure_fallback(status_code):

    client, provider = create_provider()

    client.models.generate_content.side_effect = [
        create_api_error(status_code),
        mock_response(valid_response()),
    ]

    result = provider("Instructions", "Prompt")

    assert result == valid_response()

    calls = (
        client.models.generate_content.call_args_list
    )

    assert len(calls) == 2

    assert (
        calls[0].kwargs["model"]
        == "model-primary"
    )

    assert (
        calls[1].kwargs["model"]
        == "model-fallback"
    )


# ============================================================
# NON-RETRYABLE CONFIGURATION ERRORS
# ============================================================

@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403],
)
def test_configuration_failure(status_code):

    client, provider = create_provider()

    client.models.generate_content.side_effect = (
        create_api_error(status_code)
    )

    with pytest.raises(GeminiConfigurationError):

        provider("Instructions", "Prompt")

    assert (
        client.models.generate_content.call_count
        == 1
    )


# ============================================================
# INVALID RESPONSE FALLBACK
# ============================================================

def test_invalid_json_fallback():

    client, provider = create_provider()

    invalid_response = Mock()
    invalid_response.text = "Invalid JSON"

    client.models.generate_content.side_effect = [
        invalid_response,
        mock_response(valid_response()),
    ]

    result = provider("Instructions", "Prompt")

    assert result == valid_response()

    assert (
        client.models.generate_content.call_count
        == 2
    )


def test_invalid_schema_fallback():

    client, provider = create_provider()

    client.models.generate_content.side_effect = [
        mock_response({"unexpected": "Invalid"}),
        mock_response(valid_response()),
    ]

    result = provider("Instructions", "Prompt")

    assert result == valid_response()

    assert (
        client.models.generate_content.call_count
        == 2
    )


def test_empty_response_fallback():

    client, provider = create_provider()

    empty_response = Mock()
    empty_response.text = ""

    client.models.generate_content.side_effect = [
        empty_response,
        mock_response(valid_response()),
    ]

    result = provider("Instructions", "Prompt")

    assert result == valid_response()


# ============================================================
# COMPLETE PROVIDER FAILURE
# ============================================================

def test_all_models_unavailable():

    client, provider = create_provider()

    client.models.generate_content.side_effect = [
        create_api_error(429),
        create_api_error(503),
    ]

    with pytest.raises(GeminiUnavailableError):

        provider("Instructions", "Prompt")

    assert (
        client.models.generate_content.call_count
        == len(MODELS)
    )


def test_all_models_invalid():

    client, provider = create_provider()

    client.models.generate_content.side_effect = [
        mock_response({"invalid": True}),
        mock_response({"invalid": True}),
    ]

    with pytest.raises(GeminiInvalidResponseError):

        provider("Instructions", "Prompt")

    assert (
        client.models.generate_content.call_count
        == len(MODELS)
    )


def test_unexpected_api_error():

    client, provider = create_provider()

    client.models.generate_content.side_effect = (
        create_api_error(418)
    )

    with pytest.raises(GeminiProviderError):

        provider("Instructions", "Prompt")

    assert (
        client.models.generate_content.call_count
        == 1
    )


# ============================================================
# PRIVACY-CONSCIOUS LOGGING
# ============================================================

def test_sensitive_response_not_logged(caplog):

    client, provider = create_provider()

    sensitive_text = "CONFIDENTIAL_CONTRACT_CONTENT"

    invalid_response = Mock()
    invalid_response.text = sensitive_text

    client.models.generate_content.side_effect = [
        invalid_response,
        mock_response(valid_response()),
    ]

    provider("Instructions", "Prompt")

    assert sensitive_text not in caplog.text
def test_transport_error_fallback():

    client, provider = create_provider()

    client.models.generate_content.side_effect = [
        httpx.RemoteProtocolError(
            "Server disconnected."
        ),
        mock_response(valid_response()),
    ]

    result = provider("Instructions", "Prompt")

    assert result == valid_response()

    assert (
        client.models.generate_content.call_count == 2
    )


def test_all_models_transport_failure():

    client, provider = create_provider()

    client.models.generate_content.side_effect = [
        httpx.RemoteProtocolError(
            "Server disconnected."
        ),
        httpx.ConnectError(
            "Connection failed."
        ),
    ]

    with pytest.raises(GeminiUnavailableError):

        provider("Instructions", "Prompt")

    assert (
        client.models.generate_content.call_count
        == len(MODELS)
    )
# ============================================================
# REQUEST TIMEOUT AND SDK RETRY CONFIGURATION
# ============================================================

def test_request_timeout_configuration():

    client, provider = create_provider()

    client.models.generate_content.return_value = (
        mock_response(valid_response())
    )

    provider("Instructions", "Prompt")

    config = (
        client.models.generate_content
        .call_args.kwargs["config"]
    )

    assert (
        config.http_options.timeout
        == GEMINI_REQUEST_TIMEOUT_MS
    )


def test_sdk_retry_configuration():

    client, provider = create_provider()

    client.models.generate_content.return_value = (
        mock_response(valid_response())
    )

    provider("Instructions", "Prompt")

    config = (
        client.models.generate_content
        .call_args.kwargs["config"]
    )

    assert (
        config.http_options.retry_options.attempts
        == 1
    )


# ============================================================
# REQUEST BUDGET INTEGRATION
# ============================================================

def test_successful_request_consumes_budget():

    client = Mock()

    budget = RequestBudget(max_requests=5)

    provider = GeminiProvider(
        client,
        MODELS,
        request_budget=budget,
    )

    client.models.generate_content.return_value = (
        mock_response(valid_response())
    )

    provider("Instructions", "Prompt")

    assert budget.used_requests == 1
    assert budget.remaining_requests == 4


def test_model_fallback_consumes_budget():

    client = Mock()

    budget = RequestBudget(max_requests=5)

    provider = GeminiProvider(
        client,
        MODELS,
        request_budget=budget,
    )

    client.models.generate_content.side_effect = [
        create_api_error(503),
        mock_response(valid_response()),
    ]

    provider("Instructions", "Prompt")

    assert budget.used_requests == 2
    assert budget.remaining_requests == 3


def test_budget_exhaustion_prevents_fallback():

    client = Mock()

    budget = RequestBudget(max_requests=1)

    provider = GeminiProvider(
        client,
        MODELS,
        request_budget=budget,
    )

    client.models.generate_content.side_effect = [
        create_api_error(503),
        mock_response(valid_response()),
    ]

    with pytest.raises(RequestBudgetExceededError):

        provider("Instructions", "Prompt")

    assert (
        client.models.generate_content.call_count
        == 1
    )

    assert budget.used_requests == 1
    assert budget.remaining_requests == 0