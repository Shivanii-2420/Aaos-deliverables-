from backend.app.database.base import Base
from backend.app.database.session import engine

# import all models
from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.models.test_run import TestRun
from backend.app.models.finding import Finding
from backend.app.models.risk_score import RiskScore
from backend.app.models.certificate import Certificate
from backend.app.models.evaluation_case import EvaluationCase
from backend.app.models.evaluation_result import EvaluationResult
from backend.app.models.execution_trace import ExecutionTrace
from backend.app.models.attack_result import AttackResult
from backend.app.models.assurance import (
    AssuranceDecisionRecord,
    AssuranceEvidenceRecord,
    AssuranceRunRecord,
    ToolExecutionRecord,
)
from backend.app.models.dataset import Dataset


def create_tables():
    Base.metadata.create_all(bind=engine)


def drop_tables():
    Base.metadata.drop_all(bind=engine)


def reset_database():
    drop_tables()
    create_tables()
