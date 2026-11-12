import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["REDIS_URL"] = ""
os.environ["DEFAULT_LLM_PROVIDER"] = "mock"
os.environ["API_TOKEN"] = ""

from fastapi.testclient import TestClient
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import models
from backend.app.database.base import Base
from backend.app.database.dependencies import get_db
from backend.app.engines.evaluation_engine.evaluator import Evaluator
from backend.app.engines.evaluation_engine.hallucination_detector import (
    HallucinationDetector,
)
from backend.app.engines.risk_engine.policies import RiskPolicy
from backend.app.reports.report_generator import ReportGenerator
from backend.app.config.settings import settings
from scripts.migrate_evaluation_case_scope import (
    migrate_evaluation_case_scope,
)
from backend.app.models.assurance import AssuranceEvidenceRecord
from backend.main import app


class ApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.session_factory = sessionmaker(
            bind=cls.engine,
            autocommit=False,
            autoflush=False,
        )

        def override_get_db():
            db = cls.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app, client=("127.0.0.1", 50000))

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        with self.session_factory() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.commit()

    def create_version(self, name="Evaluation reliability test"):
        agent = self.client.post("/agents", json={
            "name": name,
            "owner": "test",
            "description": "Reliability regression fixture",
        })
        self.assertEqual(agent.status_code, 200, agent.text)
        version = self.client.post(
            f"/agents/{agent.json()['id']}/versions",
            json={"version": "1.0", "model_name": "mock"},
        )
        self.assertEqual(version.status_code, 200, version.text)
        return version.json()["id"]

    def create_run(self, version_id, expected_responses=()):
        run = self.client.post(f"/versions/{version_id}/runs", json={})
        self.assertEqual(run.status_code, 200, run.text)
        run_id = run.json()["id"]
        for index, expected in enumerate(expected_responses):
            case = self.client.post("/evaluation-cases", json={
                "name": f"Reliability case {index}",
                "prompt": f"Prompt {index}",
                "expected_response": expected,
                "category": "TEST",
                "test_run_id": run_id,
            })
            self.assertEqual(case.status_code, 200, case.text)
        return run_id

    def test_metrics_and_risk_policy_have_documented_ranges(self):
        result = Evaluator.evaluate("Mock response.", "Mock response.")
        self.assertEqual(result["exact_match"], 1.0)
        self.assertEqual(result["semantic_similarity"], 1.0)
        self.assertEqual(result["score"], 1.0)
        self.assertFalse(HallucinationDetector.detect(
            "Mock response.", "Mock response."
        )["hallucination"])

        policy = RiskPolicy.evaluate(0.2, hallucinations=1)
        self.assertEqual(policy["severity"], "CRITICAL")
        self.assertLessEqual(policy["modifier"], -0.25)

    def test_local_evaluation_api_flow_and_report(self):
        agent = self.client.post("/agents", json={
            "name": "Offline test agent",
            "owner": "test",
            "description": "Automated local test",
        })
        self.assertEqual(agent.status_code, 200, agent.text)
        agent_id = agent.json()["id"]

        version = self.client.post(f"/agents/{agent_id}/versions", json={
            "version": "1.0",
            "model_name": "mock",
        })
        self.assertEqual(version.status_code, 200, version.text)
        version_id = version.json()["id"]

        run = self.client.post(f"/versions/{version_id}/runs", json={})
        self.assertEqual(run.status_code, 200, run.text)
        run_id = run.json()["id"]

        case = self.client.post("/evaluation-cases", json={
            "name": "Mock response case",
            "prompt": "A test prompt",
            "expected_response": "Mock response.",
            "category": "TEST",
        })
        self.assertEqual(case.status_code, 200, case.text)

        execution = self.client.post(f"/evaluation-execution/{run_id}")
        self.assertEqual(execution.status_code, 200, execution.text)
        self.assertEqual(execution.json()["results_created"], 1)
        self.assertEqual(execution.json()["average_score"], 1.0)
        self.assertEqual(execution.json()["status"], "COMPLETED")
        self.assertEqual(execution.json()["completed_cases"], 1)

        certificates = self.client.get("/certificates")
        self.assertEqual(certificates.status_code, 200, certificates.text)
        self.assertEqual(certificates.json()[0]["test_run_id"], run_id)
        self.assertEqual(
            certificates.json()[0]["assessment_type"],
            "INTERNAL_UNSIGNED_ASSESSMENT",
        )

        details = self.client.get(f"/evaluation-results?test_run_id={run_id}")
        self.assertEqual(details.status_code, 200, details.text)
        self.assertEqual(len(details.json()), 1)
        self.assertEqual(details.json()[0]["prompt"], "A test prompt")
        self.assertEqual(details.json()[0]["actual_response"], "Mock response.")
        self.assertEqual(
            self.client.get("/evaluation-results?test_run_id=999").status_code,
            404,
        )

        summary = self.client.get(f"/run-summary/{run_id}")
        self.assertEqual(summary.status_code, 200, summary.text)
        self.assertEqual(summary.json()["pass_count"], 1)

        dashboard = self.client.get("/dashboard/summary")
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        self.assertEqual(dashboard.json()["completed_runs"], 1)

        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(
                ReportGenerator,
                "REPORTS_DIRECTORY",
                Path(output_dir),
            ):
                report = self.client.post(f"/reports/{run_id}")
            self.assertEqual(report.status_code, 200, report.text)
            self.assertEqual(report.headers["content-type"], "application/pdf")
            self.assertTrue(report.content.startswith(b"%PDF-"))

    def test_scoped_cases_are_only_evaluated_for_their_run(self):
        agent = self.client.post("/agents", json={
            "name": "Scoped test agent",
            "owner": "test",
            "description": "Case isolation test",
        })
        version = self.client.post(
            f"/agents/{agent.json()['id']}/versions",
            json={"version": "1.0", "model_name": "mock"},
        )
        runs = [
            self.client.post(
                f"/versions/{version.json()['id']}/runs",
                json={},
            ).json()["id"]
            for _ in range(2)
        ]
        expected = ["Mock response.", "zzzzzzzzzzzz"]

        for index, run_id in enumerate(runs):
            case = self.client.post("/evaluation-cases", json={
                "name": f"Scoped case {index}",
                "prompt": f"Prompt {index}",
                "expected_response": expected[index],
                "category": "TEST",
                "test_run_id": run_id,
            })
            self.assertEqual(case.status_code, 200, case.text)

        first_result = self.client.post(f"/evaluation-execution/{runs[0]}")
        second_result = self.client.post(f"/evaluation-execution/{runs[1]}")
        self.assertEqual(first_result.status_code, 200, first_result.text)
        self.assertEqual(second_result.status_code, 200, second_result.text)
        self.assertEqual(first_result.json()["total_cases"], 1)
        self.assertEqual(first_result.json()["average_score"], 1.0)
        self.assertEqual(second_result.json()["total_cases"], 1)
        self.assertEqual(second_result.json()["average_score"], 0.0)

    def test_one_provider_failure_is_persisted_without_scoring_as_success(self):
        version_id = self.create_version()
        run_id = self.create_run(version_id, ["Expected"])
        with patch(
            "backend.app.services.evaluation_execution_service.FallbackRouter.generate",
            side_effect=RuntimeError("secret-provider-response"),
        ):
            response = self.client.post(f"/evaluation-execution/{run_id}")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "FAILED")
        self.assertEqual(response.json()["failed_cases"], 1)
        self.assertIsNone(response.json()["average_score"])
        result = self.client.get(
            f"/evaluation-results?test_run_id={run_id}"
        ).json()[0]
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertEqual(result["error_message"], "Provider request failed.")
        self.assertNotIn("secret-provider-response", str(result))
        summary = self.client.get(f"/run-summary/{run_id}").json()
        self.assertEqual(summary["status"], "FAILED")
        self.assertEqual(summary["failed_cases"], 1)
        self.assertIsNone(summary["average_score"])
        trace = self.client.get(f"/traces?test_run_id={run_id}").json()[0]
        self.assertIn("RuntimeError", trace["error"])
        self.assertNotIn("secret-provider-response", trace["error"])
        self.assertEqual(self.client.get("/certificates").json(), [])

    def test_partial_provider_failure_marks_run_failed_and_preserves_success(self):
        version_id = self.create_version()
        run_id = self.create_run(version_id, ["Mock response.", "Expected"])
        with patch(
            "backend.app.services.evaluation_execution_service.FallbackRouter.generate",
            side_effect=[
                {"provider": "mock", "content": "Mock response."},
                RuntimeError("private detail"),
            ],
        ):
            response = self.client.post(f"/evaluation-execution/{run_id}")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "FAILED")
        self.assertEqual(response.json()["completed_cases"], 1)
        self.assertEqual(response.json()["failed_cases"], 1)
        results = self.client.get(
            f"/evaluation-results?test_run_id={run_id}"
        ).json()
        self.assertCountEqual(
            [result["status"] for result in results],
            ["COMPLETED", "FAILED"],
        )
        self.assertEqual(self.client.get("/certificates").json(), [])

    def test_all_provider_failures_are_persisted_and_do_not_issue_certificate(self):
        version_id = self.create_version()
        run_id = self.create_run(version_id, ["First", "Second"])
        with patch(
            "backend.app.services.evaluation_execution_service.FallbackRouter.generate",
            side_effect=RuntimeError("private detail"),
        ):
            response = self.client.post(f"/evaluation-execution/{run_id}")

        self.assertEqual(response.json()["status"], "FAILED")
        self.assertEqual(response.json()["failed_cases"], 2)
        self.assertEqual(response.json()["completed_cases"], 0)
        self.assertEqual(
            len(self.client.get(
                f"/evaluation-results?test_run_id={run_id}"
            ).json()),
            2,
        )
        self.assertEqual(self.client.get("/certificates").json(), [])

    def test_zero_evaluable_cases_fail_without_certificate(self):
        version_id = self.create_version()
        run_id = self.create_run(version_id)
        response = self.client.post(f"/evaluation-execution/{run_id}")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "FAILED")
        self.assertEqual(response.json()["total_cases"], 0)
        self.assertEqual(
            response.json()["failure_reason"],
            "No evaluable cases were found.",
        )
        self.assertEqual(self.client.get("/certificates").json(), [])

    def test_certificate_uses_requested_run_score_and_evidence(self):
        version_id = self.create_version()
        older_run = self.create_run(version_id, ["Mock response."])
        newer_run = self.create_run(version_id, ["Different expected value"])
        self.assertEqual(
            self.client.post(f"/evaluation-execution/{older_run}").json()["status"],
            "COMPLETED",
        )
        self.assertEqual(
            self.client.post(f"/evaluation-execution/{newer_run}").json()["status"],
            "COMPLETED",
        )

        response = self.client.post("/certificates", json={
            "test_run_id": older_run,
        })
        self.assertEqual(response.status_code, 200, response.text)
        certificate = response.json()
        self.assertEqual(certificate["test_run_id"], older_run)
        self.assertEqual(certificate["score"], 1.0)
        self.assertEqual(certificate["assessment_type"], "INTERNAL_UNSIGNED_ASSESSMENT")
        evidence = __import__("json").loads(certificate["evidence"])
        self.assertEqual(evidence["test_run_id"], older_run)
        self.assertEqual(evidence["score"], 1.0)
        self.assertEqual(len(evidence["evaluation_results"]), 1)
        self.assertEqual(
            evidence["evaluation_results"][0]["expected_response"],
            "Mock response.",
        )

    def test_certificate_rejects_caller_score_failed_incomplete_and_missing_run(self):
        version_id = self.create_version()
        pending_run = self.create_run(version_id, ["Expected"])
        missing_id = self.client.post("/certificates", json={
            "test_run_id": 999,
        })
        self.assertEqual(missing_id.status_code, 404)
        missing_field = self.client.post("/certificates", json={"score": 1.0})
        self.assertEqual(missing_field.status_code, 422)
        caller_score = self.client.post("/certificates", json={
            "test_run_id": pending_run,
            "score": 1.0,
        })
        self.assertEqual(caller_score.status_code, 422)
        incomplete = self.client.post("/certificates", json={
            "test_run_id": pending_run,
        })
        self.assertEqual(incomplete.status_code, 409)

        failed_run = self.create_run(version_id, ["Expected"])
        with patch(
            "backend.app.services.evaluation_execution_service.FallbackRouter.generate",
            side_effect=RuntimeError("provider unavailable"),
        ):
            self.client.post(f"/evaluation-execution/{failed_run}")
        rejected = self.client.post("/certificates", json={
            "test_run_id": failed_run,
        })
        self.assertEqual(rejected.status_code, 409)

    def test_case_scope_migration_preserves_rows_and_is_idempotent(self):
        legacy_engine = create_engine("sqlite://")
        try:
            with legacy_engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE test_runs (id INTEGER PRIMARY KEY)"
                ))
                connection.execute(text(
                    "CREATE TABLE evaluation_cases ("
                    "id INTEGER PRIMARY KEY, "
                    "name VARCHAR(255), prompt TEXT, "
                    "expected_response TEXT, category VARCHAR(100))"
                ))
                connection.execute(text(
                    "INSERT INTO evaluation_cases "
                    "(id, name, prompt, expected_response, category) "
                    "VALUES (1, 'Existing', 'Prompt', 'Answer', 'TEST')"
                ))

            migrate_evaluation_case_scope(legacy_engine)
            migrate_evaluation_case_scope(legacy_engine)

            columns = {
                column["name"]
                for column in inspect(legacy_engine).get_columns(
                    "evaluation_cases"
                )
            }
            self.assertIn("test_run_id", columns)
            with legacy_engine.connect() as connection:
                row = connection.execute(text(
                    "SELECT id, name, test_run_id "
                    "FROM evaluation_cases WHERE id = 1"
                )).one()
            self.assertEqual(row.id, 1)
            self.assertEqual(row.name, "Existing")
            self.assertIsNone(row.test_run_id)
        finally:
            legacy_engine.dispose()

    def test_health_and_ui_are_available(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["provider_mode"], "mock")

        ui = self.client.get("/ui")
        self.assertEqual(ui.status_code, 200)
        self.assertIn("Run an evaluation", ui.text)

    def test_invalid_attack_run_returns_not_found(self):
        response = self.client.post("/attacks/run?test_run_id=999")
        self.assertEqual(response.status_code, 404)

    def test_safe_mock_attack_probes_execute_without_model_calls(self):
        response = self.client.post("/attacks/run")
        self.assertEqual(response.status_code, 200, response.text)
        results = response.json()
        self.assertEqual(len(results), 3)
        self.assertTrue(all(result["status"] == "EXECUTED" for result in results))
        self.assertTrue(all(result["success"] is False for result in results))

    def test_report_generator_does_not_overwrite_an_existing_report(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(
                ReportGenerator,
                "REPORTS_DIRECTORY",
                Path(output_dir),
            ):
                first = ReportGenerator.generate("report_1.pdf", {"Score": 1})
                second = ReportGenerator.generate("report_1.pdf", {"Score": 0})

            self.assertNotEqual(first, second)
            self.assertTrue(Path(first).exists())
            self.assertTrue(Path(second).exists())

    def test_unknown_evaluation_run_returns_not_found(self):
        response = self.client.post("/evaluation-execution/999")
        self.assertEqual(response.status_code, 404)

    def test_case_cannot_reference_unknown_run(self):
        response = self.client.post("/evaluation-cases", json={
            "name": "Orphan case",
            "prompt": "Prompt",
            "expected_response": "Answer",
            "category": "TEST",
            "test_run_id": 999,
        })
        self.assertEqual(response.status_code, 404)

    def test_adaptive_assurance_persists_explainable_mock_evidence(self):
        agent = self.client.post("/agents", json={
            "name": "EGAA test agent",
            "owner": "test",
            "description": "Adaptive assurance API integration",
        })
        version = self.client.post(
            f"/agents/{agent.json()['id']}/versions",
            json={"version": "1.0", "model_name": "mock"},
        )
        run = self.client.post(
            f"/versions/{version.json()['id']}/runs",
            json={},
        )
        run_id = run.json()["id"]
        self.client.post("/evaluation-cases", json={
            "name": "EGAA case",
            "prompt": "Prompt",
            "expected_response": "Mock response.",
            "category": "TEST",
            "test_run_id": run_id,
        })
        self.client.post(f"/evaluation-execution/{run_id}")

        assurance = self.client.post(
            f"/assurance/runs/{run_id}",
            json={"max_tests": 3, "max_seconds": 30},
        )
        self.assertEqual(assurance.status_code, 200, assurance.text)
        result = assurance.json()
        self.assertIn(result["status"], {
            "UNRESOLVED_CRITICAL_RISK",
            "EVIDENCE_INCOMPLETE",
            "EVIDENCE_COMPLETE_FOR_CONFIGURED_SCOPE",
        })
        self.assertTrue(result["selection_history"])
        self.assertTrue(result["assurance_claim"].startswith("Evidence summary"))

        stored = self.client.get(
            f"/assurance/runs/{result['assurance_run_id']}"
        )
        self.assertEqual(stored.status_code, 200, stored.text)
        self.assertTrue(stored.json()["evidence"])
        self.assertTrue(stored.json()["decisions"])

        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(
                ReportGenerator,
                "REPORTS_DIRECTORY",
                Path(output_dir),
            ):
                report = self.client.post(f"/reports/{run_id}")
        self.assertEqual(report.status_code, 200, report.text)
        self.assertTrue(report.content.startswith(b"%PDF-"))

    def test_assurance_tools_report_environment_status_and_persist_blockers(self):
        tools = self.client.get("/assurance-tools")
        self.assertEqual(tools.status_code, 200, tools.text)
        self.assertEqual(
            {item["tool"] for item in tools.json()["tools"]},
            {"garak", "deepeval"},
        )
        agent = self.client.post("/agents", json={
            "name": "Tool integration test agent",
            "owner": "test",
            "description": "Optional tool status handling",
        })
        version = self.client.post(
            f"/agents/{agent.json()['id']}/versions",
            json={"version": "1.0", "model_name": "mock"},
        )
        run_id = self.client.post(
            f"/versions/{version.json()['id']}/runs",
            json={},
        ).json()["id"]
        execution = self.client.post(
            f"/assurance-tools/deepeval/{run_id}",
            json={
                "cases": [{
                    "input": "Question",
                    "actual_output": "Answer",
                    "expected_output": "Answer",
                }],
                "metrics": ["exact_match"],
            },
        )
        self.assertEqual(execution.status_code, 200, execution.text)
        self.assertIn(
            execution.json()["status"],
            {"NOT_INSTALLED", "COMPLETED", "FAILED"},
        )
        history = self.client.get(f"/assurance-tools/runs/{run_id}")
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(history.json()[0]["tool"], "deepeval")

    def test_synthetic_benchmark_api_marks_fixtures_as_simulated(self):
        response = self.client.get("/assurance/benchmark")
        self.assertEqual(response.status_code, 200, response.text)
        report = response.json()
        self.assertEqual(len(report["scenarios"]), 3)
        self.assertTrue(all(
            item["adaptive"]["simulated"]
            for item in report["scenarios"]
        ))

    def test_local_api_token_protects_sensitive_routes_and_keeps_health_public(self):
        token = "test-only-aaos-token-with-32-chars"
        with patch.object(settings, "API_TOKEN", token):
            unauthorized = TestClient(
                app, client=("127.0.0.1", 50000)
            )
            authorized = TestClient(
                app,
                client=("127.0.0.1", 50000),
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(unauthorized.get("/health").status_code, 200)
            self.assertEqual(unauthorized.get("/agents").status_code, 401)
            self.assertEqual(authorized.get("/agents").status_code, 200)

    def test_unconfigured_api_token_restricts_non_loopback_clients(self):
        with patch.object(settings, "API_TOKEN", ""):
            remote = TestClient(app, client=("192.0.2.10", 50000))
            self.assertEqual(remote.get("/health").status_code, 200)
            self.assertEqual(remote.get("/agents").status_code, 403)

    def test_dataset_snapshot_run_keeps_case_membership_stable(self):
        blank_name = self.client.post("/datasets", json={"name": "  "})
        self.assertEqual(blank_name.status_code, 422)

        dataset = self.client.post("/datasets", json={
            "name": "Regression suite",
            "description": "Snapshot isolation test",
        })
        self.assertEqual(dataset.status_code, 200, dataset.text)
        dataset_id = dataset.json()["id"]
        added = self.client.post(f"/datasets/{dataset_id}/cases", json={
            "name": "First dataset case",
            "prompt": "Prompt 1",
            "expected_response": "Mock response.",
            "category": "QUALITY",
            "tags": ["smoke"],
            "metadata": {"source": "test"},
        })
        self.assertEqual(added.status_code, 200, added.text)
        self.assertEqual(added.json()["tags"], ["smoke"])
        self.assertEqual(added.json()["metadata"], {"source": "test"})

        agent = self.client.post("/agents", json={
            "name": "Dataset agent",
            "owner": "test",
            "description": "Dataset snapshot test",
        })
        version = self.client.post(
            f"/agents/{agent.json()['id']}/versions",
            json={"version": "1.0", "model_name": "mock"},
        )
        run = self.client.post(
            f"/datasets/{dataset_id}/versions/{version.json()['id']}/runs"
        )
        self.assertEqual(run.status_code, 200, run.text)
        snapshot_hash = run.json()["dataset_snapshot_hash"]
        self.assertEqual(run.json()["dataset_case_ids"], [added.json()["id"]])

        later = self.client.post(f"/datasets/{dataset_id}/cases", json={
            "name": "Later case",
            "prompt": "Prompt 2",
            "expected_response": "Different",
            "category": "QUALITY",
        })
        self.assertEqual(later.status_code, 200, later.text)
        execution = self.client.post(f"/evaluation-execution/{run.json()['id']}")
        self.assertEqual(execution.status_code, 200, execution.text)
        self.assertEqual(execution.json()["total_cases"], 1)
        detail = self.client.get(f"/datasets/{dataset_id}")
        self.assertEqual(len(detail.json()["cases"]), 2)
        self.assertNotEqual(
            snapshot_hash,
            self.client.get(f"/datasets/{dataset_id}").json()["snapshot_hash"],
        )

    def test_dataset_snapshot_preserves_case_content_after_dataset_changes(self):
        version_id = self.create_version()
        dataset = self.client.post("/datasets", json={
            "name": "Immutable content snapshot",
        }).json()
        case = self.client.post(f"/datasets/{dataset['id']}/cases", json={
            "name": "Original case",
            "prompt": "Original prompt",
            "expected_response": "Mock response.",
            "category": "QUALITY",
        }).json()
        run = self.client.post(
            f"/datasets/{dataset['id']}/versions/{version_id}/runs"
        ).json()

        with self.session_factory() as db:
            stored_case = db.get(models.EvaluationCase, case["id"])
            stored_case.prompt = "Changed prompt"
            stored_case.expected_response = "Changed expected response"
            db.commit()

        execution = self.client.post(
            f"/evaluation-execution/{run['id']}"
        )
        self.assertEqual(execution.status_code, 200, execution.text)
        result = self.client.get(
            f"/evaluation-results?test_run_id={run['id']}"
        ).json()[0]
        self.assertEqual(result["score"], 1.0)
        trace = self.client.get(f"/traces?test_run_id={run['id']}").json()[0]
        self.assertEqual(trace["prompt"], "Original prompt")

    def test_completed_evaluation_run_cannot_be_executed_twice(self):
        run_id = self.create_run(self.create_version(), ["Mock response."])
        first = self.client.post(f"/evaluation-execution/{run_id}")
        second = self.client.post(f"/evaluation-execution/{run_id}")

        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 409, second.text)
        results = self.client.get(
            f"/evaluation-results?test_run_id={run_id}"
        ).json()
        self.assertEqual(len(results), 1)
        certificates = [
            item for item in self.client.get("/certificates").json()
            if item["test_run_id"] == run_id
        ]
        self.assertEqual(len(certificates), 1)

    def test_alembic_upgrade_preserves_legacy_dataset_and_case_rows(self):
        with tempfile.TemporaryDirectory() as output_dir:
            database_path = Path(output_dir) / "legacy.sqlite"
            legacy_engine = create_engine(f"sqlite:///{database_path}")
            with legacy_engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE test_runs ("
                    "id INTEGER PRIMARY KEY, agent_version_id INTEGER, "
                    "status VARCHAR(50), start_time DATETIME, end_time DATETIME)"
                ))
                connection.execute(text(
                    "CREATE TABLE evaluation_cases ("
                    "id INTEGER PRIMARY KEY, name VARCHAR(255), prompt TEXT, "
                    "expected_response TEXT, category VARCHAR(100))"
                ))
                connection.execute(text(
                    "CREATE TABLE evaluation_results ("
                    "id INTEGER PRIMARY KEY, test_run_id INTEGER, "
                    "evaluation_case_id INTEGER, actual_response TEXT, "
                    "expected_response TEXT, provider VARCHAR(100), "
                    "exact_match_score FLOAT, semantic_similarity_score FLOAT, "
                    "metric_results JSON, score FLOAT, hallucination_score FLOAT, "
                    "hallucination_detected FLOAT)"
                ))
                connection.execute(text(
                    "INSERT INTO evaluation_results "
                    "(id, test_run_id, evaluation_case_id, actual_response, "
                    "expected_response, provider, exact_match_score, "
                    "semantic_similarity_score, metric_results, score, "
                    "hallucination_score, hallucination_detected) "
                    "VALUES (9, 1, 7, 'A', 'A', 'mock', 1, 1, '{}', 1, 0, 0)"
                ))
                connection.execute(text(
                    "CREATE TABLE certificates ("
                    "id INTEGER PRIMARY KEY, agent_version_id INTEGER, "
                    "certificate_no VARCHAR(100), status VARCHAR(50), "
                    "score FLOAT, evidence TEXT)"
                ))
                connection.execute(text(
                    "INSERT INTO certificates "
                    "(id, agent_version_id, certificate_no, status, score, evidence) "
                    "VALUES (3, 1, 'LEGACY-CERT', 'ISSUED', 0.8, '{}')"
                ))
                connection.execute(text(
                    "INSERT INTO evaluation_cases "
                    "(id, name, prompt, expected_response, category) "
                    "VALUES (7, 'Old case', 'Q', 'A', 'LEGACY')"
                ))
            legacy_engine.dispose()

            config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
            config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
            with patch.object(settings, "DATABASE_URL", f"sqlite:///{database_path}"):
                command.upgrade(config, "head")
                command.upgrade(config, "head")

            upgraded = create_engine(f"sqlite:///{database_path}")
            try:
                columns = {
                    item["name"]
                    for item in inspect(upgraded).get_columns("evaluation_cases")
                }
                self.assertIn("dataset_id", columns)
                self.assertIn("test_run_id", columns)
                run_columns = {
                    item["name"]
                    for item in inspect(upgraded).get_columns("test_runs")
                }
                self.assertIn("dataset_snapshot", run_columns)
                result_columns = {
                    item["name"]
                    for item in inspect(upgraded).get_columns("evaluation_results")
                }
                self.assertTrue({"status", "error_type", "error_message"} <= result_columns)
                certificate_columns = {
                    item["name"]
                    for item in inspect(upgraded).get_columns("certificates")
                }
                self.assertTrue({"test_run_id", "assessment_type"} <= certificate_columns)
                with upgraded.connect() as connection:
                    case = connection.execute(text(
                        "SELECT id, name, tags, metadata FROM evaluation_cases "
                        "WHERE id = 7"
                    )).one()
                    version_count = connection.execute(text(
                        "SELECT COUNT(*) FROM alembic_version"
                    )).scalar_one()
                    existing_result = connection.execute(text(
                        "SELECT id, score, status FROM evaluation_results WHERE id = 9"
                    )).one()
                    existing_certificate = connection.execute(text(
                        "SELECT id, certificate_no, test_run_id, assessment_type "
                        "FROM certificates WHERE id = 3"
                    )).one()
                self.assertEqual(case.id, 7)
                self.assertEqual(case.name, "Old case")
                self.assertEqual(case.tags, "[]")
                self.assertEqual(case.metadata, "{}")
                self.assertEqual(version_count, 1)
                self.assertEqual(existing_result.id, 9)
                self.assertEqual(existing_result.score, 1.0)
                self.assertEqual(existing_result.status, "COMPLETED")
                self.assertEqual(existing_certificate.id, 3)
                self.assertEqual(existing_certificate.certificate_no, "LEGACY-CERT")
                self.assertEqual(existing_certificate.assessment_type,
                                 "INTERNAL_UNSIGNED_ASSESSMENT")
            finally:
                upgraded.dispose()


if __name__ == "__main__":
    unittest.main()
