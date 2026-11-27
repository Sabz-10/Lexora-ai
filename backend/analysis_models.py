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