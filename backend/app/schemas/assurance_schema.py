from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AdaptiveRunRequest(BaseModel):
    max_tests: int = Field(default=4, ge=1, le=8)
    max_seconds: float = Field(default=60, gt=0, le=300)


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Dataset name cannot be blank")
        return normalized


class GarakExecutionRequest(BaseModel):
    model_type: Literal["test", "huggingface", "openai"] = "test"
    model_name: str = Field(default="test.Blank", min_length=1, max_length=200)
    probes: list[str] = Field(
        default_factory=lambda: ["promptinject.HijackHateHumansMini"],
        min_length=1,
        max_length=2,
    )
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    authorization_confirmed: bool = False
    external_target_confirmed: bool = False


class DeepEvalCase(BaseModel):
    input: str = Field(min_length=1, max_length=10000)
    actual_output: str = Field(max_length=10000)
    expected_output: str | None = Field(default=None, max_length=10000)


class DeepEvalExecutionRequest(BaseModel):
    cases: list[DeepEvalCase] = Field(min_length=1, max_length=100)
    metrics: list[Literal["exact_match", "answer_relevancy"]] = Field(
        min_length=1, max_length=2
    )
    threshold: float = Field(default=0.5, ge=0, le=1)
    confirm_external_judge: bool = False
