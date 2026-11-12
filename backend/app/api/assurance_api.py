from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.engines.assurance.benchmark import run_synthetic_benchmark
from backend.app.schemas.assurance_schema import (
    AdaptiveRunRequest,
    DeepEvalExecutionRequest,
    GarakExecutionRequest,
)
from backend.app.services.assurance_service import AssuranceService
from backend.app.services.tool_execution_service import ToolExecutionService

router = APIRouter(prefix="/assurance", tags=["Assurance"])


@router.get("/taxonomy")
def get_taxonomy():
    return {"dimensions": AssuranceService.taxonomy()}


@router.get("/tests")
def get_test_catalog():
    from backend.app.engines.assurance.tool_adapters import (
        DeepEvalRunner, GarakRunner,
    )

    dependencies = set()
    if DeepEvalRunner.status()["status"] == "AVAILABLE":
        dependencies.add("deepeval")
    if GarakRunner.status()["status"] == "AVAILABLE":
        dependencies.add("garak")
    return {"tests": AssuranceService.catalog(dependencies)}


@router.get("/benchmark")
def get_synthetic_benchmark():
    return run_synthetic_benchmark()


@router.post("/runs/{test_run_id}")
def execute_adaptive_assurance(
    test_run_id: int,
    payload: AdaptiveRunRequest,
    db: Session = Depends(get_db),
):
    try:
        return AssuranceService.create_run(
            test_run_id,
            db,
            payload.max_tests,
            payload.max_seconds,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/runs/{assurance_run_id}")
def get_assurance_run(
    assurance_run_id: int,
    db: Session = Depends(get_db),
):
    try:
        return AssuranceService.get_run(assurance_run_id, db)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/runs/by-test-run/{test_run_id}")
def list_assurance_runs(
    test_run_id: int,
    db: Session = Depends(get_db),
):
    return AssuranceService.list_runs(test_run_id, db)


tools_router = APIRouter(prefix="/assurance-tools", tags=["Assurance Tools"])


@tools_router.get("")
def list_tools():
    return {"tools": ToolExecutionService.available_tools()}


@tools_router.get("/runs/{test_run_id}")
def list_tool_runs(
    test_run_id: int,
    db: Session = Depends(get_db),
):
    return ToolExecutionService.get_for_run(test_run_id, db)


@tools_router.post("/garak/{test_run_id}")
def run_garak(
    test_run_id: int,
    payload: GarakExecutionRequest,
    db: Session = Depends(get_db),
):
    try:
        return ToolExecutionService.run_garak(
            test_run_id,
            db,
            payload.model_type,
            payload.model_name,
            payload.probes,
            payload.timeout_seconds,
            payload.authorization_confirmed,
            payload.external_target_confirmed,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@tools_router.post("/deepeval/{test_run_id}")
def run_deepeval(
    test_run_id: int,
    payload: DeepEvalExecutionRequest,
    db: Session = Depends(get_db),
):
    try:
        return ToolExecutionService.run_deepeval(
            test_run_id,
            db,
            [case.model_dump() for case in payload.cases],
            payload.metrics,
            payload.threshold,
            payload.confirm_external_judge,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
