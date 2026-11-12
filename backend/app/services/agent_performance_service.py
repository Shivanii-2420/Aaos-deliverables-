from sqlalchemy.orm import Session

from backend.app.models.agent_version import AgentVersion
from backend.app.models.test_run import TestRun
from backend.app.models.evaluation_result import EvaluationResult


class AgentPerformanceService:

    @staticmethod
    def get_performance(agent_id: int, db: Session):

        versions = (
            db.query(AgentVersion)
            .filter(AgentVersion.agent_id == agent_id)
            .all()
        )

        versions_summary = []

        for v in versions:
            # runs for this version
            runs = (
                db.query(TestRun)
                .filter(TestRun.agent_version_id == v.id)
                .all()
            )

            run_ids = [r.id for r in runs]

            if not run_ids:
                versions_summary.append({
                    "version_id": v.id,
                    "version": v.version,
                    "total_runs": 0,
                    "total_results": 0,
                    "average_score": 0.0,
                    "average_exact_match": 0.0,
                    "average_semantic_similarity": 0.0,
                    "average_hallucination_score": 0.0
                })
                continue

            results = (
                db.query(EvaluationResult)
                .filter(EvaluationResult.test_run_id.in_(run_ids))
                .all()
            )

            total_results = len(results)

            if total_results == 0:
                versions_summary.append({
                    "version_id": v.id,
                    "version": v.version,
                    "total_runs": len(runs),
                    "total_results": 0,
                    "average_score": 0.0,
                    "average_exact_match": 0.0,
                    "average_semantic_similarity": 0.0,
                    "average_hallucination_score": 0.0
                })
                continue

            avg_score = sum(r.score for r in results) / total_results
            avg_exact = sum(r.exact_match_score for r in results) / total_results
            avg_semantic = sum(r.semantic_similarity_score for r in results) / total_results
            avg_hallucination = sum(r.hallucination_score for r in results) / total_results

            versions_summary.append({
                "version_id": v.id,
                "version": v.version,
                "total_runs": len(runs),
                "total_results": total_results,
                "average_score": round(avg_score, 4),
                "average_exact_match": round(avg_exact, 4),
                "average_semantic_similarity": round(avg_semantic, 4),
                "average_hallucination_score": round(avg_hallucination, 4)
            })

        return {
            "agent_id": agent_id,
            "versions": versions_summary
        }
