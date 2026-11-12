from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from backend.app.database.session import (
    get_db
)

from backend.app.services.report_service import (
    ReportService
)

router = APIRouter()


@router.post(
    "/reports/{test_run_id}"
)
def generate_report(
    test_run_id: int,
    db: Session = Depends(get_db)
):
    try:
        pdf_path = ReportService.generate(
            test_run_id,
            db
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"aaos_report_{test_run_id}.pdf"
    )