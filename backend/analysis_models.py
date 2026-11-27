from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


# ============================================================
# REUSABLE TYPES
# ============================================================

RiskLevel = Literal["green", "yellow", "red"]

NonEmptyText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]


# ============================================================
# BASE RESPONSE MODEL
# ============================================================

class StrictResponseModel(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )


# ============================================================
# CLAUSE FINDING
# ============================================================

class ClauseFinding(StrictResponseModel):

    text: NonEmptyText

    risk: RiskLevel

    category: NonEmptyText

    explanation: NonEmptyText

    why_risky: str

    questions: list[NonEmptyText] = Field(
        max_length=2,
    )

    @model_validator(mode="after")
    def validate_risk_explanation(self):

        if self.risk == "green":
            if self.why_risky.strip():
                raise ValueError(
                    "Green findings must not have "
                    "a risk explanation."
                )

        else:
            if not self.why_risky.strip():
                raise ValueError(
                    "Yellow and red findings require "
                    "a risk explanation."
                )

        return self


# ============================================================
# KEY FACT
# ============================================================

class KeyFact(StrictResponseModel):

    label: NonEmptyText

    value: NonEmptyText

    source_excerpt: NonEmptyText


# ============================================================
# RAW CHUNK ANALYSIS RESPONSE
# ============================================================

class ChunkAnalysisResponse(StrictResponseModel):

    clauses: list[ClauseFinding]

    key_facts: list[KeyFact]
# ============================================================
# VERIFIED SOURCE EVIDENCE
# ============================================================

class SourceEvidence(StrictResponseModel):

    excerpt: NonEmptyText

    chunk_id: int = Field(ge=1)

    start_offset: int = Field(ge=0)

    end_offset: int = Field(gt=0)

    source_block_ids: list[int] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_offsets(self):

        if self.end_offset <= self.start_offset:
            raise ValueError(
                "End offset must be greater than start offset."
            )

        return self
# ============================================================
# VERIFIED CLAUSE FINDING
# ============================================================

class VerifiedClauseFinding(StrictResponseModel):

    finding: ClauseFinding

    evidence: list[SourceEvidence] = Field(
        min_length=1,
    )


# ============================================================
# VERIFIED KEY FACT
# ============================================================

class VerifiedKeyFact(StrictResponseModel):

    fact: KeyFact

    evidence: list[SourceEvidence] = Field(
        min_length=1,
    )


# ============================================================
# VERIFIED CHUNK ANALYSIS RESULT
# ============================================================

class VerifiedChunkResult(StrictResponseModel):

    chunk_id: int = Field(ge=1)

    clauses: list[VerifiedClauseFinding]

    key_facts: list[VerifiedKeyFact]
# ============================================================
# DOCUMENT-LEVEL ANALYSIS RESULT
# ============================================================

class DocumentAnalysisResult(StrictResponseModel):

    strategy: Literal["single_pass", "multi_chunk"]

    total_estimated_tokens: int = Field(ge=0)

    total_chunks: int = Field(ge=1)

    chunk_results: list[VerifiedChunkResult]

    @property
    def completed_chunks(self) -> int:

        return len(self.chunk_results)

    @property
    def total_clauses(self) -> int:

        return sum(
            len(result.clauses)
            for result in self.chunk_results
        )

    @property
    def total_key_facts(self) -> int:

        return sum(
            len(result.key_facts)
            for result in self.chunk_results
        )

    @model_validator(mode="after")
    def validate_completion(self):

        if self.completed_chunks != self.total_chunks:

            raise ValueError(
                "Not all document chunks were analyzed."
            )

        chunk_ids = [
            result.chunk_id
            for result in self.chunk_results
        ]

        expected_ids = list(
            range(1, self.total_chunks + 1)
        )

        if chunk_ids != expected_ids:

            raise ValueError(
                "Chunk results are missing, duplicated "
                "or incorrectly ordered."
            )

        if (
            self.strategy == "single_pass"
            and self.total_chunks != 1
        ):

            raise ValueError(
                "Single-pass analysis requires one chunk."
            )

        return self
# ============================================================
# DOCUMENT ANALYSIS EXECUTION RESULT
# ============================================================

class AnalysisExecutionResult(StrictResponseModel):

    analysis: DocumentAnalysisResult

    requests_used: int = Field(ge=0)

    request_limit: int = Field(ge=1)

    @property
    def requests_remaining(self) -> int:

        return (
            self.request_limit
            - self.requests_used
        )

    @model_validator(mode="after")
    def validate_request_usage(self):

        if self.requests_used > self.request_limit:

            raise ValueError(
                "Request usage exceeds the allocated budget."
            )

        return self