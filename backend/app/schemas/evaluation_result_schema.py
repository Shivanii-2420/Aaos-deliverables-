from pydantic import BaseModel


class EvaluationResultResponse(BaseModel):

    id: int

    test_run_id: int

    evaluation_case_id: int

    status: str

    error_type: str | None

    error_message: str | None

    expected_response: str

    actual_response: str

    provider: str

    exact_match_score: float

    semantic_similarity_score: float

    metric_results: dict[str, float]

    hallucination_score: float

    hallucination_detected: float

    score: float

    class Config:
        from_attributes = True