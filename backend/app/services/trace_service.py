from sqlalchemy.orm import Session

from backend.app.engines.flight_recorder.trace_store import TraceStore


class TraceService:

    @staticmethod
    def get_traces(db: Session, test_run_id: int | None = None):
        if test_run_id is not None:
            return [
                trace
                for trace in TraceStore.get_all(db)
                if trace.test_run_id == test_run_id
            ]

        return TraceStore.get_all(db)

    @staticmethod
    def save_trace(db: Session, trace_data: dict):
        return TraceStore.save(db, trace_data)
