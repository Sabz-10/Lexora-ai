from threading import Lock

from config import MAX_API_REQUESTS_PER_DOCUMENT


# ============================================================
# CUSTOM EXCEPTION
# ============================================================

class RequestBudgetExceededError(RuntimeError):
    pass


# ============================================================
# THREAD-SAFE REQUEST BUDGET
# ============================================================

class RequestBudget:

    def __init__(
        self,
        max_requests: int = MAX_API_REQUESTS_PER_DOCUMENT,
    ):

        if max_requests < 1:

            raise ValueError(
                "Request budget must be at least 1."
            )

        self._max_requests = max_requests
        self._used_requests = 0
        self._lock = Lock()

    @property
    def max_requests(self) -> int:

        return self._max_requests

    @property
    def used_requests(self) -> int:

        with self._lock:

            return self._used_requests

    @property
    def remaining_requests(self) -> int:

        with self._lock:

            return (
                self._max_requests
                - self._used_requests
            )

    def consume(self) -> None:

        with self._lock:

            if (
                self._used_requests
                >= self._max_requests
            ):

                raise RequestBudgetExceededError(
                    "Document API request budget exhausted."
                )

            self._used_requests += 1