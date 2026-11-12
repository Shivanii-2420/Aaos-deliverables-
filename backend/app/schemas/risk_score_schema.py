from pydantic import BaseModel


class RiskScoreResponse(BaseModel):
    id: int
    security_score: float
    reliability_score: float
    overall_score: float

    class Config:
        from_attributes = True