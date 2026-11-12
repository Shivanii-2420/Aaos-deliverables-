from pydantic import BaseModel
from datetime import datetime


class TraceResponse(BaseModel):
    id: int
    test_run_id: int | None
    prompt: str
    response: str
    provider: str | None
    started_at: datetime
    ended_at: datetime | None
    latency_ms: float
    tokens_used: int
    cost: float
    error: str | None

    class Config:
        from_attributes = True
