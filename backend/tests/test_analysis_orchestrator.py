from threading import Lock, Barrier
import time
import pytest

from pydantic import ValidationError

from config import SINGLE_PASS_MAX_TOKENS

from document_models import (
    DocumentBlock,
    ParsedDocument,
)

from analysis_models import (
    DocumentAnalysisResult,
    VerifiedChunkResult,
)

from analysis_orchestrator import analyze_document


# ============================================================
# TEST HELPERS
# ============================================================

def create_document(text):

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

    text = "A" * (
        SINGLE_PASS_MAX_TOKENS * 4 + 1
    )

    return create_document(text)


def mock_provider(system_instruction, prompt):

    return {
        "clauses": [],
        "key_facts": [],
    }


def create_chunk_result(chunk_id):

    return VerifiedChunkResult(
        chunk_id=chunk_id,
        clauses=[],
        key_facts=[],
    )


# ============================================================
# SINGLE-PASS ANALYSIS
# ============================================================

def test_single_pass_analysis():

    document = create_document(
        "Monthly rent is Rs. 5000."
    )

    result = analyze_document(
        document,
        mock_provider,
    )

    assert isinstance(
        result,
        DocumentAnalysisResult,
    )

    assert result.strategy == "single_pass"
    assert result.total_chunks == 1
    assert result.completed_chunks == 1


def test_single_pass_provider_call():

    document = create_document(
        "Sample contract."
    )

    calls = []

    def provider(system_instruction, prompt):

        calls.append(prompt)

        return mock_provider(
            system_instruction,
            prompt,
        )

    analyze_document(document, provider)

    assert len(calls) == 1


# ============================================================
# MULTI-CHUNK ANALYSIS
# ============================================================

def test_multi_chunk_analysis():

    document = create_large_document()

    result = analyze_document(
        document,
        mock_provider,
    )

    assert result.strategy == "multi_chunk"
    assert result.total_chunks > 1

    assert (
        result.completed_chunks
        == result.total_chunks
    )


def test_multi_chunk_provider_calls():

    document = create_large_document()

    calls = []

    def provider(system_instruction, prompt):

        calls.append(prompt)

        return mock_provider(
            system_instruction,
            prompt,
        )

    result = analyze_document(
        document,
        provider,
    )

    assert len(calls) == result.total_chunks


def test_chunk_execution_order():

    document = create_large_document()

    result = analyze_document(
        document,
        mock_provider,
    )

    chunk_ids = [
        chunk.chunk_id
        for chunk in result.chunk_results
    ]

    assert chunk_ids == list(
        range(1, result.total_chunks + 1)
    )


# ============================================================
# FINDING AGGREGATION
# ============================================================

def test_finding_aggregation():

    text = "Monthly rent is Rs. 5000."

    document = create_document(text)

    def provider(system_instruction, prompt):

        return {
            "clauses": [
                {
                    "text": text,
                    "risk": "green",
                    "category": "Rent",
                    "explanation":
                        "Defines monthly rent.",
                    "why_risky": "",
                    "questions": [],
                }
            ],
            "key_facts": [
                {
                    "label": "Monthly rent",
                    "value": "Rs. 5000",
                    "source_excerpt": text,
                }
            ],
        }

    result = analyze_document(
        document,
        provider,
        "rental",
    )

    assert result.total_clauses == 1
    assert result.total_key_facts == 1


def test_empty_findings_aggregation():

    document = create_document(
        "Sample contract."
    )

    result = analyze_document(
        document,
        mock_provider,
    )

    assert result.total_clauses == 0
    assert result.total_key_facts == 0


# ============================================================
# FAILURE HANDLING
# ============================================================

def test_empty_document():

    document = create_document("")

    calls = []

    def provider(system_instruction, prompt):

        calls.append(prompt)

        return mock_provider(
            system_instruction,
            prompt,
        )

    with pytest.raises(ValueError):

        analyze_document(document, provider)

    assert calls == []


def test_provider_failure_propagates():

    document = create_document(
        "Sample contract."
    )

    def failing_provider(system_instruction, prompt):

        raise RuntimeError(
            "Simulated provider failure"
        )

    with pytest.raises(
        RuntimeError,
        match="Simulated provider failure",
    ):

        analyze_document(
            document,
            failing_provider,
        )


def test_multi_chunk_stops_on_failure():

    document = create_large_document()

    calls = []

    def provider(system_instruction, prompt):

        calls.append(prompt)

        if len(calls) == 2:

            raise RuntimeError(
                "Second chunk failed"
            )

        return mock_provider(
            system_instruction,
            prompt,
        )

    with pytest.raises(
        RuntimeError,
        match="Second chunk failed",
    ):

        analyze_document(
    document,
    provider,
    max_workers=1,
)

    assert len(calls) == 2


# ============================================================
# DOCUMENT RESULT VALIDATION
# ============================================================

def test_incomplete_analysis_rejected():

    with pytest.raises(ValidationError):

        DocumentAnalysisResult(
            strategy="multi_chunk",
            total_estimated_tokens=25000,
            total_chunks=3,
            chunk_results=[
                create_chunk_result(1),
                create_chunk_result(2),
            ],
        )


def test_duplicate_chunk_ids_rejected():

    with pytest.raises(ValidationError):

        DocumentAnalysisResult(
            strategy="multi_chunk",
            total_estimated_tokens=25000,
            total_chunks=2,
            chunk_results=[
                create_chunk_result(1),
                create_chunk_result(1),
            ],
        )


def test_out_of_order_chunks_rejected():

    with pytest.raises(ValidationError):

        DocumentAnalysisResult(
            strategy="multi_chunk",
            total_estimated_tokens=25000,
            total_chunks=2,
            chunk_results=[
                create_chunk_result(2),
                create_chunk_result(1),
            ],
        )


def test_missing_chunk_id_rejected():

    with pytest.raises(ValidationError):

        DocumentAnalysisResult(
            strategy="multi_chunk",
            total_estimated_tokens=25000,
            total_chunks=2,
            chunk_results=[
                create_chunk_result(1),
                create_chunk_result(3),
            ],
        )


def test_invalid_single_pass_result():

    with pytest.raises(ValidationError):

        DocumentAnalysisResult(
            strategy="single_pass",
            total_estimated_tokens=1000,
            total_chunks=2,
            chunk_results=[
                create_chunk_result(1),
                create_chunk_result(2),
            ],
        )
# ============================================================
# CONCURRENCY TESTS
# ============================================================

def test_invalid_worker_count():

    document = create_document(
        "Sample contract."
    )

    with pytest.raises(ValueError):

        analyze_document(
            document,
            mock_provider,
            max_workers=0,
        )


def test_concurrent_execution():

    document = create_large_document()

    barrier = Barrier(2)

    lock = Lock()

    calls = 0

    def provider(system_instruction, prompt):

        nonlocal calls

        with lock:

            calls += 1
            call_number = calls

        if call_number <= 2:

            barrier.wait(timeout=5)

        return mock_provider(
            system_instruction,
            prompt,
        )

    result = analyze_document(
        document,
        provider,
        max_workers=2,
    )

    assert calls == result.total_chunks

    assert (
        result.completed_chunks
        == result.total_chunks
    )


def test_concurrency_limit():

    document = create_large_document()

    lock = Lock()

    active_requests = 0
    peak_requests = 0

    def provider(system_instruction, prompt):

        nonlocal active_requests
        nonlocal peak_requests

        with lock:

            active_requests += 1

            peak_requests = max(
                peak_requests,
                active_requests,
            )

        try:

            time.sleep(0.05)

            return mock_provider(
                system_instruction,
                prompt,
            )

        finally:

            with lock:

                active_requests -= 1

    result = analyze_document(
        document,
        provider,
        max_workers=2,
    )

    assert 1 <= peak_requests <= 2

    assert active_requests == 0

    assert (
        result.completed_chunks
        == result.total_chunks
    )


def test_single_worker_execution():

    document = create_large_document()

    lock = Lock()

    active_requests = 0
    peak_requests = 0

    def provider(system_instruction, prompt):

        nonlocal active_requests
        nonlocal peak_requests

        with lock:

            active_requests += 1

            peak_requests = max(
                peak_requests,
                active_requests,
            )

        try:

            return mock_provider(
                system_instruction,
                prompt,
            )

        finally:

            with lock:

                active_requests -= 1

    analyze_document(
        document,
        provider,
        max_workers=1,
    )

    assert peak_requests == 1


def test_concurrent_result_order():

    document = create_large_document()

    result = analyze_document(
        document,
        mock_provider,
        max_workers=2,
    )

    chunk_ids = [
        chunk.chunk_id
        for chunk in result.chunk_results
    ]

    assert chunk_ids == list(
        range(1, result.total_chunks + 1)
    )


def test_concurrent_failure_propagates():

    document = create_large_document()

    def failing_provider(system_instruction, prompt):

        raise RuntimeError(
            "Concurrent provider failure"
        )

    with pytest.raises(
        RuntimeError,
        match="Concurrent provider failure",
    ):

        analyze_document(
            document,
            failing_provider,
            max_workers=2,
        )