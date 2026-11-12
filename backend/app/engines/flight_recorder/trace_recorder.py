from datetime import datetime


class TraceRecorder:

    @staticmethod
    def record(
        prompt: str,
        response: str,
        provider: str,
        started_at: datetime,
        ended_at: datetime,
        latency_ms: float,
        error: str | None = None,
        tokens_used: int = 0,
        cost: float = 0.0,
        test_run_id: int | None = None
    ):

        return {
            "test_run_id": test_run_id,
            "prompt": prompt,
            "response": response,
            "provider": provider,
            "started_at": started_at,
            "ended_at": ended_at,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "cost": cost,
            "error": error
        }
