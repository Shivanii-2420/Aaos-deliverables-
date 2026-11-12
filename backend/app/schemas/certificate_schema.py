from pydantic import BaseModel


class CertificateResponse(BaseModel):
    id: int
    agent_version_id: int
    test_run_id: int | None
    certificate_no: str
    status: str
    assessment_type: str
    score: float
    evidence: str | None

    class Config:
        from_attributes = True