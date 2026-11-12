from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db

from backend.app.schemas.agent_version_schema import (
    AgentVersionCreate,
    AgentVersionResponse
)

from backend.app.services.agent_version_service import (
    AgentVersionService
)

router = APIRouter(
    prefix="/agents",
    tags=["Agent Versions"]
)


@router.post(
    "/{agent_id}/versions",
    response_model=AgentVersionResponse
)
def create_version(
    agent_id: int,
    payload: AgentVersionCreate,
    db: Session = Depends(get_db)
):

    return AgentVersionService.create_version(
        db,
        agent_id,
        payload
    )


@router.get(
    "/{agent_id}/versions",
    response_model=list[AgentVersionResponse]
)
def get_versions(
    agent_id: int,
    db: Session = Depends(get_db)
):

    return AgentVersionService.get_versions(
        db,
        agent_id
    )