from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.models.certificate import Certificate
from backend.app.schemas.certificate_schema import CertificateResponse
from backend.app.services.certificate_service import (
    CertificateService
)


router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"]
)


@router.get("", response_model=list[CertificateResponse])
def get_certificates(db: Session = Depends(get_db)):
    return db.query(Certificate).all()


class CertificateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_run_id: int


@router.post("", response_model=CertificateResponse)
def create_certificate(payload: CertificateCreate, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    try:
        return CertificateService.create_certificate(payload.test_run_id, db)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
