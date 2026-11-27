import pytest
from pydantic import ValidationError

from analysis_models import (
    ClauseFinding,
    KeyFact,
    ChunkAnalysisResponse,
)


# ============================================================
# SAMPLE DATA
# ============================================================

def valid_clause():
    return {
        "text": "The tenant must pay a late fee of Rs. 500.",
        "risk": "yellow",
        "category": "Payment",
        "explanation": "Late payments attract a fee.",
        "why_risky": "The fee increases payment obligations.",
        "questions": [
            "Can the late fee be reduced?"
        ],
    }


def valid_fact():
    return {
        "label": "Late fee",
        "value": "Rs. 500",
        "source_excerpt":
            "The tenant must pay a late fee of Rs. 500.",
    }


# ============================================================
# CLAUSE VALIDATION
# ============================================================

def test_valid_clause():
    clause = ClauseFinding.model_validate(valid_clause())

    assert clause.risk == "yellow"
    assert clause.category == "Payment"


def test_invalid_risk():
    data = valid_clause()
    data["risk"] = "extreme"

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


def test_missing_required_field():
    data = valid_clause()
    del data["explanation"]

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


def test_unexpected_field():
    data = valid_clause()
    data["unknown_field"] = "unexpected"

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


def test_empty_clause_text():
    data = valid_clause()
    data["text"] = "   "

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


def test_invalid_questions_type():
    data = valid_clause()
    data["questions"] = 123

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


def test_too_many_questions():
    data = valid_clause()
    data["questions"] = ["Q1", "Q2", "Q3"]

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


def test_valid_green_clause():
    data = valid_clause()
    data["risk"] = "green"
    data["why_risky"] = ""

    clause = ClauseFinding.model_validate(data)

    assert clause.risk == "green"
    assert clause.why_risky == ""


def test_green_with_risk_explanation():
    data = valid_clause()
    data["risk"] = "green"

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


@pytest.mark.parametrize("risk", ["yellow", "red"])
def test_missing_risk_explanation(risk):
    data = valid_clause()
    data["risk"] = risk
    data["why_risky"] = "   "

    with pytest.raises(ValidationError):
        ClauseFinding.model_validate(data)


# ============================================================
# KEY FACT VALIDATION
# ============================================================

def test_valid_key_fact():
    fact = KeyFact.model_validate(valid_fact())

    assert fact.label == "Late fee"
    assert fact.value == "Rs. 500"


def test_missing_source_excerpt():
    data = valid_fact()
    del data["source_excerpt"]

    with pytest.raises(ValidationError):
        KeyFact.model_validate(data)


def test_invalid_fact_value_type():
    data = valid_fact()
    data["value"] = 500

    with pytest.raises(ValidationError):
        KeyFact.model_validate(data)


# ============================================================
# COMPLETE CHUNK RESPONSE VALIDATION
# ============================================================

def test_valid_chunk_response():
    data = {
        "clauses": [valid_clause()],
        "key_facts": [valid_fact()],
    }

    result = ChunkAnalysisResponse.model_validate(data)

    assert len(result.clauses) == 1
    assert len(result.key_facts) == 1

    assert isinstance(result.clauses[0], ClauseFinding)
    assert isinstance(result.key_facts[0], KeyFact)


def test_empty_chunk_response():
    data = {
        "clauses": [],
        "key_facts": [],
    }

    result = ChunkAnalysisResponse.model_validate(data)

    assert result.clauses == []
    assert result.key_facts == []


def test_invalid_nested_clause():
    clause = valid_clause()
    clause["risk"] = "unknown"

    data = {
        "clauses": [clause],
        "key_facts": [],
    }

    with pytest.raises(ValidationError):
        ChunkAnalysisResponse.model_validate(data)