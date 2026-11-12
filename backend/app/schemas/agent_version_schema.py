from pydantic import BaseModel
from datetime import datetime


class AgentVersionCreate(BaseModel):
    # Accept agent_id in the body to support the convenience endpoint
    agent_id: int | None = None
    version: str
    model_name: str
    prompt_hash: str | None = None


class AgentVersionResponse(BaseModel):
    id: int
    agent_id: int
    version: str
    model_name: str
    prompt_hash: str | None
    created_at: datetime

    class Config:
        from_attributes = True