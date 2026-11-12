from sqlalchemy.orm import Session

from backend.app.models.test_run import TestRun


class TestRunService:

    @staticmethod
    def create_test_run(
        db: Session,
        agent_version_id: int
    ):

        run = TestRun(
            agent_version_id=agent_version_id,
            status="CREATED"
        )

        db.add(run)

        db.commit()

        db.refresh(run)

        return run

    @staticmethod
    def get_test_runs(
        db: Session,
        agent_version_id: int
    ):

        return (
            db.query(TestRun)
            .filter(
                TestRun.agent_version_id ==
                agent_version_id
            )
            .all()
        )