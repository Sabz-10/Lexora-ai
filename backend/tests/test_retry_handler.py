from unittest.mock import Mock

import pytest

from retry_handler import (
    execute_with_retry,
    calculate_retry_delay,
    RetryExhaustedError,
)

from gemini_provider import (
    GeminiUnavailableError,
    GeminiInvalidResponseError,
    GeminiConfigurationError,
)

from chunk_analyzer import EvidenceValidationError


# ============================================================
# DISABLE ACTUAL WAITING DURING TESTS
# ============================================================

@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch):

    sleeper = Mock()

    monkeypatch.setattr(
        "retry_handler.time.sleep",
        sleeper,
    )

    return sleeper


# ============================================================
# SUCCESSFUL EXECUTION
# ============================================================

def test_success_without_retry(mock_sleep):

    operation = Mock(return_value="Success")

    result = execute_with_retry(operation)

    assert result == "Success"
    assert operation.call_count == 1

    mock_sleep.assert_not_called()


# ============================================================
# RETRY RECOVERY
# ============================================================

@pytest.mark.parametrize(
    "exception_class",
    [
        GeminiUnavailableError,
        GeminiInvalidResponseError,
        EvidenceValidationError,
    ],
)
def test_retryable_error_recovery(
    exception_class,
    mock_sleep,
):

    operation = Mock(
        side_effect=[
            exception_class("Temporary failure"),
            "Recovered",
        ]
    )

    result = execute_with_retry(operation)

    assert result == "Recovered"
    assert operation.call_count == 2

    assert mock_sleep.call_count == 1


def test_success_on_final_attempt(mock_sleep):

    operation = Mock(
        side_effect=[
            GeminiUnavailableError("Failure 1"),
            GeminiUnavailableError("Failure 2"),
            "Success",
        ]
    )

    result = execute_with_retry(
        operation,
        max_retries=2,
    )

    assert result == "Success"
    assert operation.call_count == 3
    assert mock_sleep.call_count == 2


# ============================================================
# RETRY EXHAUSTION
# ============================================================

def test_retry_exhaustion(mock_sleep):

    operation = Mock(
        side_effect=GeminiUnavailableError(
            "Service unavailable"
        )
    )

    with pytest.raises(RetryExhaustedError):

        execute_with_retry(
            operation,
            max_retries=2,
        )

    assert operation.call_count == 3
    assert mock_sleep.call_count == 2


def test_zero_retries(mock_sleep):

    operation = Mock(
        side_effect=GeminiUnavailableError(
            "Service unavailable"
        )
    )

    with pytest.raises(RetryExhaustedError):

        execute_with_retry(
            operation,
            max_retries=0,
        )

    assert operation.call_count == 1

    mock_sleep.assert_not_called()


# ============================================================
# NON-RETRYABLE FAILURES
# ============================================================

@pytest.mark.parametrize(
    "exception_class",
    [
        GeminiConfigurationError,
        ValueError,
        TypeError,
        RuntimeError,
    ],
)
def test_non_retryable_failure(
    exception_class,
    mock_sleep,
):

    operation = Mock(
        side_effect=exception_class(
            "Permanent failure"
        )
    )

    with pytest.raises(exception_class):

        execute_with_retry(operation)

    assert operation.call_count == 1

    mock_sleep.assert_not_called()


def test_negative_retry_count():

    operation = Mock()

    with pytest.raises(ValueError):

        execute_with_retry(
            operation,
            max_retries=-1,
        )

    operation.assert_not_called()


# ============================================================
# EXPONENTIAL BACKOFF
# ============================================================

def test_exponential_backoff(monkeypatch):

    monkeypatch.setattr(
        "retry_handler.random.uniform",
        lambda minimum, maximum: 0,
    )

    delays = [
        calculate_retry_delay(number)
        for number in range(1, 5)
    ]

    assert delays == [
        1.0,
        2.0,
        4.0,
        8.0,
    ]


def test_backoff_maximum_limit():

    delay = calculate_retry_delay(
        retry_number=10,
        max_delay=8.0,
    )

    assert delay <= 8.0


def test_jitter_range(monkeypatch):

    monkeypatch.setattr(
        "retry_handler.random.uniform",
        lambda minimum, maximum: maximum,
    )

    delay = calculate_retry_delay(
        retry_number=1,
        base_delay=1.0,
    )

    assert delay == 1.25


def test_invalid_retry_number():

    with pytest.raises(ValueError):

        calculate_retry_delay(
            retry_number=0,
        )


@pytest.mark.parametrize(
    "base_delay,max_delay",
    [
        (0, 8),
        (-1, 8),
        (1, 0),
        (1, -8),
    ],
)
def test_invalid_delay_configuration(
    base_delay,
    max_delay,
):

    with pytest.raises(ValueError):

        calculate_retry_delay(
            retry_number=1,
            base_delay=base_delay,
            max_delay=max_delay,
        )


# ============================================================
# LOGGING PRIVACY
# ============================================================

def test_sensitive_error_not_logged(caplog):

    sensitive_text = "CONFIDENTIAL_CONTRACT_CONTENT"

    operation = Mock(
        side_effect=GeminiUnavailableError(
            sensitive_text
        )
    )

    with pytest.raises(RetryExhaustedError):

        execute_with_retry(
            operation,
            max_retries=1,
        )

    assert sensitive_text not in caplog.text