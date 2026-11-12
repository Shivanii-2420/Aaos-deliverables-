from dataclasses import asdict
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.config.settings import settings
from backend.app.engines.assurance.tool_adapters import (
    DeepEvalRunner,
    GarakRunner,
    ToolResult,
)
from backend.app.models.assurance import ToolExecutionRecord
from backend.app.models.test_run import TestRun


class ToolExecutionService:
    REPORT_ROOT = Path(__file__).resolve().parents[3] / "reports" / "assurance"

    @staticmethod
    def available_tools() -> list[dict[str, Any]]:
        return [GarakRunner.status(), DeepEvalRunner.status()]

    @staticmethod
    def run_garak(
        test_run_id: int,
        db: Session,
        model_type: str,
        model_name: str,
        probes: list[str],
        timeout_seconds: int,
        authorization_confirmed: bool,
        external_target_confirmed: bool,
    ) -> dict[str, Any]:
        if db.get(TestRun, test_run_id) is None:
            raise LookupError(f"Test run {test_run_id} was not found")
        result = GarakRunner.run(
            model_type=model_type,
            model_name=model_name,
            probes=probes,
            output_root=ToolExecutionService.REPORT_ROOT / "garak",
            authorization_confirmed=authorization_confirmed,
            external_target_confirmed=external_target_confirmed,
            timeout_seconds=timeout_seconds,
        )
        return ToolExecutionService._persist(test_run_id, result, {
            "model_type": model_type,
            "model_name": model_name,
            "probes": probes,
            "timeout_seconds": timeout_seconds,
            "authorization_confirmed": authorization_confirmed,
            "external_target_confirmed": external_target_confirmed,
        }, db)

    @staticmethod
    def run_deepeval(
        test_run_id: int,
        db: Session,
        cases: list[dict[str, str | None]],
        metrics: list[str],
        threshold: float,
        confirm_external_judge: bool,
    ) -> dict[str, Any]:
        if db.get(TestRun, test_run_id) is None:
            raise LookupError(f"Test run {test_run_id} was not found")
        judge_model = settings.DEEPEVAL_JUDGE_MODEL or None
        allow_judge = (
            confirm_external_judge
            and settings.DEEPEVAL_ALLOW_JUDGE_CALLS
            and judge_model is not None
        )
        result = DeepEvalRunner.run(
            cases=cases,
            metrics=metrics,
            threshold=threshold,
            judge_model=judge_model,
            allow_judge_calls=allow_judge,
        )
        return ToolExecutionService._persist(test_run_id, result, {
            "metrics": metrics,
            "threshold": threshold,
            "judge_model": judge_model,
            "external_judge_confirmed": confirm_external_judge,
            "judge_calls_enabled_by_configuration":
                settings.DEEPEVAL_ALLOW_JUDGE_CALLS,
        }, db)

    @staticmethod
    def _persist(
        test_run_id: int,
        result: ToolResult,
        configuration: dict[str, Any],
        db: Session,
    ) -> dict[str, Any]:
        row = ToolExecutionRecord(
            test_run_id=test_run_id,
            execution_id=result.execution_id,
            tool=result.tool,
            status=result.status,
            version=result.version,
            started_at=result.started_at,
            ended_at=result.ended_at,
            duration_seconds=result.duration_seconds,
            configuration=configuration,
            findings=result.findings,
            metrics=result.metrics,
            error=result.error,
            artifact_paths=result.artifact_paths,
            original_metadata=result.original_metadata,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return ToolExecutionService._serialize(row)

    @staticmethod
    def get_for_run(test_run_id: int, db: Session) -> list[dict[str, Any]]:
        rows = (
            db.query(ToolExecutionRecord)
            .filter(ToolExecutionRecord.test_run_id == test_run_id)
            .order_by(ToolExecutionRecord.id.desc())
            .all()
        )
        return [ToolExecutionService._serialize(row) for row in rows]

    @staticmethod
    def _serialize(row: ToolExecutionRecord) -> dict[str, Any]:
        return {
            "execution_id": row.execution_id,
            "test_run_id": row.test_run_id,
            "tool": row.tool,
            "status": row.status,
            "version": row.version,
            "started_at": row.started_at,
            "ended_at": row.ended_at,
            "duration_seconds": row.duration_seconds,
            "configuration": row.configuration,
            "findings": row.findings,
            "metrics": row.metrics,
            "error": row.error,
            "artifact_paths": row.artifact_paths,
            "original_metadata": row.original_metadata,
        }
