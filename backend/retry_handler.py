import logging
import random
import time

from typing import Callable, TypeVar

from pydantic import ValidationError

from config import MAX_RETRIES

from chunk_analyzer import EvidenceValidationError

from gemini_provider import (
    GeminiUnavailableError,
    GeminiInvalidResponseError,
)


logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================
# RETRYABLE EXCEPTIONS
# ============================================================

RETRYABLE_EXCEPTIONS = (
    GeminiUnavailableError,
    GeminiInvalidResponseError,
    EvidenceValidationError,
    ValidationError,
)


# ============================================================
# RETRY EXHAUSTION EXCEPTION
# ============================================================

class RetryExhaustedError(RuntimeError):
    pass


# ============================================================
# EXPONENTIAL BACKOFF WITH JITTER
# ============================================================

def calculate_retry_delay(
    retry_number: int,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
) -> float:

    if retry_number < 1:

        raise ValueError(
            "Retry number must be at least 1."
        )

    if base_delay <= 0 or max_delay <= 0:

        raise ValueError(
            "Retry delays must be positive."
        )

    delay = min(
        max_delay,
        base_delay * (2 ** (retry_number - 1)),
    )

    jitter = random.uniform(
        0,
        delay * 0.25,
    )

    return min(
        max_delay,
        delay + jitter,
    )


# ============================================================
# CONTROLLED RETRY EXECUTION
# ============================================================

def execute_with_retry(
    operation: Callable[[], T],
    max_retries: int = MAX_RETRIES,
) -> T:

    if max_retries < 0:

        raise ValueError(
            "max_retries cannot be negative."
        )

    total_attempts = max_retries + 1

    for attempt in range(
        1,
        total_attempts + 1,
    ):

        try:

            return operation()

        except RETRYABLE_EXCEPTIONS as exc:

            if attempt == total_attempts:

                logger.warning(
                    "Retry budget exhausted: "
                    "attempts=%s error_type=%s",
                    attempt,
                    type(exc).__name__,
                )

                raise RetryExhaustedError(
                    f"Operation failed after "
                    f"{total_attempts} attempts."
                ) from None

            delay = calculate_retry_delay(
                retry_number=attempt,
            )

            logger.warning(
                "Retryable failure: "
                "attempt=%s/%s error_type=%s "
                "retry_delay=%.2fs",
                attempt,
                total_attempts,
                type(exc).__name__,
                delay,
            )

            time.sleep(delay)

    raise RuntimeError(
        "Unexpected retry execution state."
    )