from typing import Literal

from pydantic import BaseModel, Field, field_validator


class HallucinationEvaluationRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    response: str = Field(min_length=1, max_length=20000)
    reference_context: str | list[str] | None = None

    @field_validator("prompt", "response")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must contain at least one non-whitespace character")
        return value.strip()

    @field_validator("reference_context")
    @classmethod
    def limit_reference_context(
        cls,
        value: str | list[str] | None,
    ) -> str | list[str] | None:
        if isinstance(value, str) and len(value) > 50000:
            raise ValueError("Reference context must not exceed 50000 characters")
        if isinstance(value, list):
            if len(value) > 50 or any(not isinstance(item, str) for item in value):
                raise ValueError("Provide at most 50 text reference documents")
            if sum(len(item) for item in value) > 50000:
                raise ValueError("Reference documents must not exceed 50000 characters total")
        return value


class HallucinationFinding(BaseModel):
    claim: str
    category: str
    status: Literal["supported", "contradicted", "unsupported", "unverifiable"]
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    evidence: str | None
    explanation: str


class HallucinationCategoryScore(BaseModel):
    score: float | None
    status: Literal["working", "partial", "not_implemented"]
    claims_evaluated: int
    description: str


class HallucinationEvaluationResponse(BaseModel):
    claim_count: int
    supported: int
    contradicted: int
    unsupported: int
    unverifiable: int
    overall_hallucination_score: float | None
    category_scores: dict[str, HallucinationCategoryScore]
    claims: list[HallucinationFinding]
    problematic_claims: list[HallucinationFinding]
    risk: dict[str, float | str] | None
    scoring: dict[str, object]
    limitations: list[str]
