from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.database.dependencies import get_db

from backend.app.schemas.agent_schema import (
    AgentCreate,
    AgentResponse
)

from backend.app.services.agent_service import AgentService


router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


@router.post(
    "",
    response_model=AgentResponse
)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db)
):

    return AgentService.create_agent(
        db,
        payload
    )


@router.get(
    "",
    response_model=list[AgentResponse]
)
def get_agents(
    db: Session = Depends(get_db)
):

    return AgentService.get_agents(db)