from pydantic import BaseModel
from datetime import datetime


class AgentCreate(BaseModel):
    name: str
    # Make owner optional so callers that don't provide it (e.g. via CLI)
    # can still create agents. The DB column is made nullable as well.
    owner: str | None = None
    description: str | None = None


class AgentResponse(BaseModel):
    id: int
    name: str
    owner: str | None
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True