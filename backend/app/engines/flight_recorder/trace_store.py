from sqlalchemy.orm import Session

from backend.app.models.execution_trace import ExecutionTrace


class TraceStore:

    @staticmethod
    def save(db: Session, trace_data: dict):
        trace = ExecutionTrace(
            test_run_id=trace_data.get("test_run_id"),
            prompt=trace_data.get("prompt", ""),
            response=trace_data.get("response", ""),
            provider=trace_data.get("provider", "unknown"),
            started_at=trace_data.get("started_at"),
            ended_at=trace_data.get("ended_at"),
            latency_ms=trace_data.get("latency_ms", 0.0),
            tokens_used=trace_data.get("tokens_used", 0),
            cost=trace_data.get("cost", 0.0),
            error=trace_data.get("error")
        )

        db.add(trace)
        db.commit()
        db.refresh(trace)

        return trace

    @staticmethod
    def get_all(db: Session):
        return db.query(ExecutionTrace).all()
