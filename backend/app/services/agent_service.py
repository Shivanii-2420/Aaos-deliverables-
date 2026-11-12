from sqlalchemy.orm import Session

from backend.app.models.agent import Agent

from backend.app.schemas.agent_schema import AgentCreate


class AgentService:

    @staticmethod
    def create_agent(
        db: Session,
        payload: AgentCreate
    ) -> Agent:

        agent = Agent(
            name=payload.name,
            owner=payload.owner,
            description=payload.description
        )

        db.add(agent)

        db.commit()

        db.refresh(agent)

        return agent

    @staticmethod
    def get_agents(
        db: Session
    ):

        return db.query(Agent).all()

    @staticmethod
    def get_agent(
        db: Session,
        agent_id: int
    ):

        return (
            db.query(Agent)
            .filter(Agent.id == agent_id)
            .first()
        )