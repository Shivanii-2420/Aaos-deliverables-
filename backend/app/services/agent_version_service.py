from sqlalchemy.orm import Session

from backend.app.models.agent_version import AgentVersion

from backend.app.schemas.agent_version_schema import (
    AgentVersionCreate
)


class AgentVersionService:

    @staticmethod
    def create_version(
        db: Session,
        agent_id: int,
        payload: AgentVersionCreate
    ):

        version = AgentVersion(
            agent_id=agent_id,
            version=payload.version,
            model_name=payload.model_name,
            prompt_hash=payload.prompt_hash
        )

        db.add(version)

        db.commit()

        db.refresh(version)

        return version

    @staticmethod
    def get_versions(
        db: Session,
        agent_id: int
    ):

        return (
            db.query(AgentVersion)
            .filter(
                AgentVersion.agent_id == agent_id
            )
            .all()
        )