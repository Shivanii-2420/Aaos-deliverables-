from pydantic import BaseModel
from datetime import datetime


class TestRunResponse(BaseModel):
    id: int
    agent_version_id: int
    status: str
    start_time: datetime
    end_time: datetime | None

    class Config:
        from_attributes = True