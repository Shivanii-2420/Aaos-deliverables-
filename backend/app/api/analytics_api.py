from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from backend.app.database.dependencies import (
    get_db
)

from backend.app.models.agent import Agent
from backend.app.models.agent_version import (
    AgentVersion
)
from backend.app.models.test_run import TestRun
from backend.app.models.evaluation_result import (
    EvaluationResult
)
from backend.app.models.risk_score import RiskScore
from backend.app.models.finding import Finding

from backend.app.services.evaluation_summary_service import (
    EvaluationSummaryService
)
from backend.app.services.agent_performance_service import (
    AgentPerformanceService
)

router = APIRouter(
    tags=["Analytics"]
)


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    runs = (
        db.query(TestRun)
        .order_by(TestRun.id.desc())
        .limit(10)
        .all()
    )
    result_scores = [
        row[0]
        for row in db.query(EvaluationResult.score)
        .filter(EvaluationResult.status == "COMPLETED")
        .all()
        if row[0] is not None
    ]

    return {
        "total_agents": db.query(Agent).count(),
        "total_runs": db.query(TestRun).count(),
        "completed_runs": db.query(TestRun).filter(
            TestRun.status == "COMPLETED"
        ).count(),
        "failed_runs": db.query(TestRun).filter(
            TestRun.status == "FAILED"
        ).count(),
        "average_score": (
            round(sum(result_scores) / len(result_scores), 4)
            if result_scores else None
        ),
        "risk_score_count": db.query(RiskScore).count(),
        "finding_count": db.query(Finding).count(),
        "recent_runs": [
            {
                "id": run.id,
                "status": run.status,
                "agent_version_id": run.agent_version_id,
                "start_time": run.start_time.isoformat()
                if run.start_time else None,
            }
            for run in runs
        ],
    }


@router.get("/system-summary")
def system_summary(
    db: Session = Depends(get_db)
):

    total_agents = (
        db.query(Agent).count()
    )

    total_versions = (
        db.query(AgentVersion).count()
    )

    total_runs = (
        db.query(TestRun).count()
    )

    total_results = (
        db.query(EvaluationResult).count()
    )

    return {
        "total_agents": total_agents,
        "total_versions": total_versions,
        "total_runs": total_runs,
        "total_results": total_results
    }


@router.get("/run-summary/{test_run_id}")
def run_summary(
    test_run_id: int,
    db: Session = Depends(get_db)
):

    return (
        EvaluationSummaryService
        .summarize_run(
            test_run_id,
            db
        )
    )


@router.get("/agent-performance/{agent_id}")
def agent_performance(
    agent_id: int,
    db: Session = Depends(get_db)
):

    return AgentPerformanceService.get_performance(agent_id, db)
