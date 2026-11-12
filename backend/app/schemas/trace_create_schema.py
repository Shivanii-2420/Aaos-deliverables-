from pydantic import BaseModel
from datetime import datetime

class TraceCreate(BaseModel):
    test_run_id: int | None = None
    prompt: str
    response: str
    provider: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    error: str | None = None

    class Config:
        from_attributes = True
