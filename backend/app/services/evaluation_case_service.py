from sqlalchemy.orm import Session

from backend.app.models.evaluation_case import (
    EvaluationCase
)

from backend.app.schemas.evaluation_case_schema import (
    EvaluationCaseCreate
)


class EvaluationCaseService:

    @staticmethod
    def create_case(
        db: Session,
        payload: EvaluationCaseCreate,
        dataset_id: int | None = None,
    ):

        case = EvaluationCase(
            name=payload.name,
            prompt=payload.prompt,
            expected_response=payload.expected_response,
            category=payload.category,
            test_run_id=payload.test_run_id,
            tags=payload.tags,
            metadata_json=payload.metadata,
            dataset_id=dataset_id if dataset_id is not None else payload.dataset_id,
        )

        db.add(case)
        if case.dataset_id is not None:
            from backend.app.models.dataset import Dataset

            dataset = db.get(Dataset, case.dataset_id)
            if dataset is None:
                raise LookupError(f"Dataset {case.dataset_id} was not found")
            dataset.version += 1
        db.commit()

        db.refresh(case)

        return case

    @staticmethod
    def get_cases(
        db: Session,
        test_run_id: int | None = None
    ):

        query = db.query(EvaluationCase)
        if test_run_id is not None:
            query = query.filter(
                (EvaluationCase.test_run_id == test_run_id)
                | (EvaluationCase.test_run_id.is_(None))
            )
        return query.order_by(EvaluationCase.id).all()