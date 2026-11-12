from pydantic import BaseModel


class ReportResponse(BaseModel):
    pdf_path: str

    class Config:
        from_attributes = True
