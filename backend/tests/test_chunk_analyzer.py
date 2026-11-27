import pytest

from pydantic import ValidationError

from document_models import (
    DocumentBlock,
    ParsedDocument,
    DocumentChunk,
)

from analysis_models import VerifiedChunkResult

from chunk_analyzer import (
    analyze_chunk,
    EvidenceValidationError,
)

from prompt_builder import CHUNK_SYSTEM_INSTRUCTIONS


# ============================================================
# TEST HELPERS
# ============================================================

def create_document():

    text = "The tenant must pay a late fee of Rs. 500."

    block = DocumentBlock(
        block_id=1,
        text=text,
        source_type="page",
        source_number=1,
        start_offset=0,
        end_offset=len(text),
    )

    return ParsedDocument(
        filename="sample.pdf",
        file_type="pdf",
        blocks=[block],
        total_characters=len(text),
    )


def create_chunk(document):

    text = document.full_text

    return DocumentChunk(
        chunk_id=1,
        text=text,
        start_offset=0,
        end_offset=len(text),
        estimated_tokens=(len(text) + 3) // 4,
        source_block_ids=[1],
    )


def valid_response():

    return {
        "clauses": [
            {
                "text":
                    "The tenant must pay a late fee of Rs. 500.",
                "risk": "yellow",
                "category": "Payment",
                "explanation":
                    "Late payments attract a fee.",
                "why_risky":
                    "The fee increases payment obligations.",
                "questions": [
                    "Can the late fee be reduced?"
                ],
            }
        ],
        "key_facts": [
            {
                "label": "Late fee",
                "value": "Rs. 500",
                "source_excerpt":
                    "The tenant must pay a late fee of Rs. 500.",
            }
        ],
    }


# ============================================================
# MOCK AI PROVIDER
# ============================================================

def mock_provider(system_instruction, prompt):

    return valid_response()


# ============================================================
# SUCCESSFUL ANALYSIS
# ============================================================

def test_successful_chunk_analysis():

    document = create_document()
    chunk = create_chunk(document)

    result = analyze_chunk(
        chunk,
        document,
        mock_provider,
        "rental",
    )

    assert isinstance(result, VerifiedChunkResult)

    assert result.chunk_id == 1
    assert len(result.clauses) == 1
    assert len(result.key_facts) == 1

    assert result.clauses[0].finding.risk == "yellow"


def test_clause_evidence_attached():

    document = create_document()
    chunk = create_chunk(document)

    result = analyze_chunk(
        chunk,
        document,
        mock_provider,
    )

    evidence = result.clauses[0].evidence[0]

    assert evidence.chunk_id == 1
    assert evidence.source_block_ids == [1]

    assert document.full_text[
        evidence.start_offset:evidence.end_offset
    ] == evidence.excerpt


def test_key_fact_evidence_attached():

    document = create_document()
    chunk = create_chunk(document)

    result = analyze_chunk(
        chunk,
        document,
        mock_provider,
    )

    fact = result.key_facts[0]

    assert fact.fact.value == "Rs. 500"
    assert len(fact.evidence) == 1

    assert (
        fact.evidence[0].excerpt
        == fact.fact.source_excerpt
    )


# ============================================================
# PROVIDER INTERFACE
# ============================================================

def test_provider_receives_correct_inputs():

    document = create_document()
    chunk = create_chunk(document)

    calls = []

    def provider(system_instruction, prompt):

        calls.append((system_instruction, prompt))

        return valid_response()

    analyze_chunk(
        chunk,
        document,
        provider,
        "rental",
    )

    assert len(calls) == 1

    system_instruction, prompt = calls[0]

    assert system_instruction == CHUNK_SYSTEM_INSTRUCTIONS
    assert chunk.text in prompt
    assert "security deposit" in prompt


def test_provider_failure_propagates():

    document = create_document()
    chunk = create_chunk(document)

    def failing_provider(system_instruction, prompt):

        raise RuntimeError("Simulated provider failure")

    with pytest.raises(
        RuntimeError,
        match="Simulated provider failure",
    ):

        analyze_chunk(
            chunk,
            document,
            failing_provider,
        )


# ============================================================
# STRUCTURED RESPONSE VALIDATION
# ============================================================

def test_invalid_response_structure():

    document = create_document()
    chunk = create_chunk(document)

    def invalid_provider(system_instruction, prompt):

        return {
            "unexpected_field": "Invalid response"
        }

    with pytest.raises(ValidationError):

        analyze_chunk(
            chunk,
            document,
            invalid_provider,
        )


def test_invalid_risk_rejected():

    document = create_document()
    chunk = create_chunk(document)

    def invalid_provider(system_instruction, prompt):

        response = valid_response()

        response["clauses"][0]["risk"] = "extreme"

        return response

    with pytest.raises(ValidationError):

        analyze_chunk(
            chunk,
            document,
            invalid_provider,
        )


# ============================================================
# FABRICATED EVIDENCE
# ============================================================

def test_fabricated_clause_rejected():

    document = create_document()
    chunk = create_chunk(document)

    def fabricated_provider(system_instruction, prompt):

        response = valid_response()

        response["clauses"][0]["text"] = (
            "The tenant must pay Rs. 50000."
        )

        return response

    with pytest.raises(EvidenceValidationError):

        analyze_chunk(
            chunk,
            document,
            fabricated_provider,
        )


def test_fabricated_fact_excerpt_rejected():

    document = create_document()
    chunk = create_chunk(document)

    def fabricated_provider(system_instruction, prompt):

        response = valid_response()

        response["key_facts"][0]["source_excerpt"] = (
            "The security deposit is Rs. 100000."
        )

        return response

    with pytest.raises(EvidenceValidationError):

        analyze_chunk(
            chunk,
            document,
            fabricated_provider,
        )


# ============================================================
# EMPTY RESPONSE
# ============================================================

def test_empty_response():

    document = create_document()
    chunk = create_chunk(document)

    def empty_provider(system_instruction, prompt):

        return {
            "clauses": [],
            "key_facts": [],
        }

    result = analyze_chunk(
        chunk,
        document,
        empty_provider,
    )

    assert result.clauses == []
    assert result.key_facts == []


# ============================================================
# CHUNK INTEGRITY
# ============================================================

@pytest.mark.parametrize(
    "corruption",
    ["offset", "content"],
)
def test_invalid_chunk_prevents_provider_call(corruption):

    document = create_document()
    chunk = create_chunk(document)

    if corruption == "offset":
        chunk.start_offset = -1

    else:
        chunk.text = "Modified contract."

    calls = []

    def provider(system_instruction, prompt):

        calls.append(prompt)

        return valid_response()

    with pytest.raises(ValueError):

        analyze_chunk(
            chunk,
            document,
            provider,
        )

    assert calls == []


# ============================================================
# RESPONSE ATOMICITY
# ============================================================

def test_partially_invalid_response_rejected():

    document = create_document()
    chunk = create_chunk(document)

    def provider(system_instruction, prompt):

        response = valid_response()

        invalid_clause = response["clauses"][0].copy()

        invalid_clause["text"] = "An invented penalty."

        response["clauses"].append(invalid_clause)

        return response

    with pytest.raises(EvidenceValidationError):

        analyze_chunk(
            chunk,
            document,
            provider,
        )