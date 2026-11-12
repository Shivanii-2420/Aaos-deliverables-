from pydantic import BaseModel


class AttackResultResponse(BaseModel):
    id: int
    test_run_id: int | None
    attack_name: str
    prompt: str
    status: str
    response: str | None
    risk: str
    success: bool
    reason: str | None

    class Config:
        from_attributes = True
