from concurrent.futures import ThreadPoolExecutor

import pytest

from request_budget import (
    RequestBudget,
    RequestBudgetExceededError,
)

from config import MAX_API_REQUESTS_PER_DOCUMENT


# ============================================================
# BUDGET INITIALIZATION
# ============================================================

def test_default_budget():

    budget = RequestBudget()

    assert (
        budget.max_requests
        == MAX_API_REQUESTS_PER_DOCUMENT
    )

    assert budget.used_requests == 0


def test_custom_budget():

    budget = RequestBudget(max_requests=5)

    assert budget.max_requests == 5
    assert budget.remaining_requests == 5


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_budget(limit):

    with pytest.raises(ValueError):

        RequestBudget(max_requests=limit)


# ============================================================
# REQUEST CONSUMPTION
# ============================================================

def test_single_request_consumption():

    budget = RequestBudget(max_requests=5)

    budget.consume()

    assert budget.used_requests == 1
    assert budget.remaining_requests == 4


def test_multiple_request_consumption():

    budget = RequestBudget(max_requests=5)

    for _ in range(3):

        budget.consume()

    assert budget.used_requests == 3
    assert budget.remaining_requests == 2


def test_exact_budget_limit():

    budget = RequestBudget(max_requests=3)

    for _ in range(3):

        budget.consume()

    assert budget.used_requests == 3
    assert budget.remaining_requests == 0


def test_budget_exhaustion():

    budget = RequestBudget(max_requests=1)

    budget.consume()

    with pytest.raises(RequestBudgetExceededError):

        budget.consume()

    assert budget.used_requests == 1
    assert budget.remaining_requests == 0


# ============================================================
# BUDGET ISOLATION
# ============================================================

def test_independent_document_budgets():

    budget1 = RequestBudget(max_requests=5)
    budget2 = RequestBudget(max_requests=5)

    budget1.consume()

    assert budget1.used_requests == 1
    assert budget2.used_requests == 0


# ============================================================
# CONCURRENT REQUEST CONSUMPTION
# ============================================================

def test_concurrent_budget_consumption():

    budget = RequestBudget(max_requests=20)

    def consume_request(index):

        try:

            budget.consume()

            return True

        except RequestBudgetExceededError:

            return False

    with ThreadPoolExecutor(max_workers=8) as executor:

        results = list(
            executor.map(
                consume_request,
                range(100),
            )
        )

    assert results.count(True) == 20
    assert results.count(False) == 80

    assert budget.used_requests == 20
    assert budget.remaining_requests == 0