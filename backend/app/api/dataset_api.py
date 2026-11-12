import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db
from backend.app.models.agent_version import AgentVersion
from backend.app.models.dataset import Dataset
from backend.app.models.evaluation_case import EvaluationCase
from backend.app.models.test_run import TestRun
from backend.app.schemas.evaluation_case_schema import (
    EvaluationCaseCreate,
    EvaluationCaseResponse,
)
from backend.app.schemas.assurance_schema import DatasetCreate
from backend.app.services.evaluation_case_service import EvaluationCaseService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


def _snapshot(dataset_id: int, db: Session):
    cases = (
        db.query(EvaluationCase)
        .filter(EvaluationCase.dataset_id == dataset_id)
        .order_by(EvaluationCase.id)
        .all()
    )
    serialized = [
        {
            "id": case.id,
            "name": case.name,
            "prompt": case.prompt,
            "expected_response": case.expected_response,
            "category": case.category,
            "tags": case.tags or [],
            "metadata": case.metadata_json or {},
        }
        for case in cases
    ]
    snapshot_hash = hashlib.sha256(
        json.dumps(
            serialized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return cases, snapshot_hash


@router.post("")
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    dataset = Dataset(
        name=payload.name,
        description=payload.description,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    _, snapshot_hash = _snapshot(dataset.id, db)
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "version": dataset.version,
        "snapshot_hash": snapshot_hash,
        "case_count": 0,
    }


@router.get("")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).order_by(Dataset.id.desc()).all()
    output = []
    for dataset in datasets:
        cases, snapshot_hash = _snapshot(dataset.id, db)
        output.append({
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "version": dataset.version,
            "snapshot_hash": snapshot_hash,
            "case_count": len(cases),
        })
    return output


@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    cases, snapshot_hash = _snapshot(dataset_id, db)
    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "version": dataset.version,
        "snapshot_hash": snapshot_hash,
        "cases": [
            EvaluationCaseResponse.model_validate(case).model_dump()
            for case in cases
        ],
    }


@router.post("/{dataset_id}/cases", response_model=EvaluationCaseResponse)
def add_dataset_case(
    dataset_id: int,
    payload: EvaluationCaseCreate,
    db: Session = Depends(get_db),
):
    if db.get(Dataset, dataset_id) is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if payload.test_run_id is not None:
        raise HTTPException(
            status_code=422,
            detail="Dataset cases cannot be scoped directly to a test run",
        )
    try:
        return EvaluationCaseService.create_case(
            db, payload, dataset_id=dataset_id
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{dataset_id}/versions/{version_id}/runs")
def create_dataset_run(
    dataset_id: int,
    version_id: int,
    db: Session = Depends(get_db),
):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if db.get(AgentVersion, version_id) is None:
        raise HTTPException(status_code=404, detail="Agent version not found")
    cases, snapshot_hash = _snapshot(dataset_id, db)
    run = TestRun(
        agent_version_id=version_id,
        status="CREATED",
        dataset_id=dataset_id,
        dataset_version=dataset.version,
        dataset_snapshot_hash=snapshot_hash,
        dataset_case_ids=[case.id for case in cases],
        dataset_snapshot=[
            {
                "id": case.id,
                "name": case.name,
                "prompt": case.prompt,
                "expected_response": case.expected_response,
                "category": case.category,
                "tags": case.tags or [],
                "metadata": case.metadata_json or {},
            }
            for case in cases
        ],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {
        "id": run.id,
        "agent_version_id": run.agent_version_id,
        "status": run.status,
        "dataset_id": run.dataset_id,
        "dataset_version": run.dataset_version,
        "dataset_snapshot_hash": run.dataset_snapshot_hash,
        "dataset_case_ids": run.dataset_case_ids,
    }
