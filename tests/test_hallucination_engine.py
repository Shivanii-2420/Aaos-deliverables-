import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("DEFAULT_LLM_PROVIDER", "mock")
os.environ.setdefault("API_TOKEN", "")

from fastapi.testclient import TestClient

from backend.app.engines.evaluation_engine.evaluator import Evaluator
from backend.app.engines.evaluation_engine.hallucination_engine import (
    HallucinationEvaluationEngine,
)
from backend.main import app


class HallucinationEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, client=("127.0.0.1", 50000))

    def test_exact_factual_response_is_supported(self):
        result = HallucinationEvaluationEngine.evaluate(
            "What is the capital?",
            "Paris is the capital of France.",
            "Paris is the capital of France.",
        )
        self.assertEqual(result["supported"], 1)
        self.assertEqual(result["contradicted"], 0)
        self.assertEqual(result["overall_hallucination_score"], 100)

    def test_fabricated_unsupported_and_entity_claims_are_not_called_false(self):
        result = HallucinationEvaluationEngine.evaluate(
            "Where is the tower?",
            "The Eiffel Tower is in Rome.",
            "The Eiffel Tower is in Paris.",
        )
        self.assertEqual(result["unsupported"], 1)
        self.assertEqual(result["contradicted"], 0)
        self.assertEqual(result["claims"][0]["category"], "entity_errors")
        self.assertEqual(result["problematic_claims"][0]["status"], "unsupported")

    def test_numeric_context_contradiction_is_detected(self):
        result = HallucinationEvaluationEngine.evaluate(
            "What is the population?",
            "The population is 12 million.",
            "The population is 10 million.",
        )
        self.assertEqual(result["contradicted"], 1)
        self.assertEqual(result["claims"][0]["category"], "factual_errors")
        self.assertEqual(result["claims"][0]["severity"], "HIGH")

    def test_year_conflict_is_a_temporal_finding(self):
        result = HallucinationEvaluationEngine.evaluate(
            "When was it founded?",
            "The company was founded in 2019.",
            "The company was founded in 2015.",
        )
        self.assertEqual(result["contradicted"], 1)
        self.assertEqual(result["claims"][0]["category"], "temporal_inaccuracies")

    def test_missing_reference_context_keeps_claims_unverifiable(self):
        result = HallucinationEvaluationEngine.evaluate(
            "Who discovered this?",
            "Ada Lovelace discovered it.",
        )
        self.assertEqual(result["unverifiable"], 1)
        self.assertIsNone(result["overall_hallucination_score"])
        self.assertIsNone(result["risk"])

    def test_citation_marker_must_exist_in_structured_references(self):
        result = HallucinationEvaluationEngine.evaluate(
            "Summarize the source.",
            "The result is established [2].",
            ["[1] Source document."],
        )
        self.assertEqual(
            result["claims"][0]["category"],
            "citation_hallucinations",
        )
        self.assertEqual(result["unsupported"], 1)

    def test_citation_without_structured_reference_is_unverifiable(self):
        result = HallucinationEvaluationEngine.evaluate(
            "Summarize the source.",
            "The result is established [2].",
            "A source without explicit citation identifiers.",
        )
        self.assertEqual(result["unverifiable"], 1)

    def test_category_registry_marks_unimplemented_checks(self):
        categories = {
            item["name"]: item["status"]
            for item in HallucinationEvaluationEngine.categories()
        }
        self.assertEqual(categories["unsupported_claims"], "working")
        self.assertEqual(categories["relationship_errors"], "not_implemented")
        self.assertEqual(categories["instruction_inconsistencies"], "not_implemented")

    def test_unverifiable_claims_do_not_lower_score_or_duplicate_categories(self):
        result = HallucinationEvaluationEngine.evaluate(
            "Answer.",
            "Paris is the capital of France. A second unsupported detail.",
            "Paris is the capital of France.",
        )
        self.assertEqual(result["claim_count"], 2)
        self.assertEqual(result["supported"], 1)
        self.assertEqual(result["unsupported"], 1)
        self.assertEqual(result["overall_hallucination_score"], 75)
        self.assertEqual(
            sum(item["claims_evaluated"] for item in result["category_scores"].values()),
            result["claim_count"],
        )

    def test_offline_api_validates_inputs_and_returns_risk(self):
        response = self.client.post("/evaluation/hallucination", json={
            "prompt": "What is the population?",
            "response": "The population is 12 million.",
            "reference_context": "The population is 10 million.",
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["contradicted"], 1)
        self.assertIn("severity", response.json()["risk"])

        empty = self.client.post("/evaluation/hallucination", json={
            "prompt": " ",
            "response": "Text",
        })
        self.assertEqual(empty.status_code, 422)

        malformed = self.client.post("/evaluation/hallucination", json={
            "prompt": "Question",
            "response": ["not", "text"],
        })
        self.assertEqual(malformed.status_code, 422)

        oversized_context = self.client.post("/evaluation/hallucination", json={
            "prompt": "Question",
            "response": "Text",
            "reference_context": "x" * 50001,
        })
        self.assertEqual(oversized_context.status_code, 422)

    def test_existing_evaluator_contract_is_unchanged(self):
        result = Evaluator.evaluate("Mock response.", "Mock response.")
        self.assertEqual(result["exact_match"], 1.0)
        self.assertEqual(result["semantic_similarity"], 1.0)
        self.assertEqual(result["score"], 1.0)


if __name__ == "__main__":
    unittest.main()
