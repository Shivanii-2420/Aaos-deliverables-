import types
import unittest
from unittest.mock import patch

from backend.app.adapters import litellm_client
from backend.app.adapters.azure_openai_adapter import AzureOpenAIAdapter
from backend.app.adapters.claude_adapter import ClaudeAdapter
from backend.app.adapters.gemini_adapter import GeminiAdapter
from backend.app.services.llm_router.health_monitor import HealthMonitor


class LiteLLMClientTests(unittest.TestCase):
    def test_completion_has_timeout_and_returns_text(self):
        response = types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content="answer")
                )
            ]
        )
        with patch.object(
            litellm_client, "completion", return_value=response
        ) as completion:
            result = litellm_client.generate_text(
                "Test provider", "test-model", "prompt", "test-key"
            )

        self.assertEqual(result, "answer")
        self.assertEqual(
            completion.call_args.kwargs["timeout"],
            litellm_client.REQUEST_TIMEOUT_SECONDS,
        )

    def test_missing_api_key_fails_before_network_call(self):
        with patch.object(litellm_client, "completion") as completion:
            with self.assertRaisesRegex(
                litellm_client.ProviderClientError,
                "API key is not configured",
            ):
                litellm_client.generate_text(
                    "Test provider", "test-model", "prompt", ""
                )
        completion.assert_not_called()

    def test_transient_connection_error_retries_once(self):
        class TransientError(Exception):
            pass

        response = types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content="answer")
                )
            ]
        )
        with patch.object(
            litellm_client, "APIConnectionError", TransientError
        ), patch.object(
            litellm_client,
            "completion",
            side_effect=[TransientError("private provider details"), response],
        ) as completion, patch.object(litellm_client.time, "sleep"):
            result = litellm_client.generate_text(
                "Test provider", "test-model", "prompt", "test-key"
            )

        self.assertEqual(result, "answer")
        self.assertEqual(completion.call_count, 2)

    def test_provider_error_is_sanitized(self):
        with patch.object(
            litellm_client, "completion", side_effect=ValueError("private detail")
        ):
            with self.assertRaises(RuntimeError) as raised:
                litellm_client.generate_text(
                    "Test provider", "test-model", "prompt", "test-key"
                )

        self.assertNotIn("private detail", str(raised.exception))


class ProviderAdapterTests(unittest.TestCase):
    def test_provider_adapters_use_shared_bounded_client(self):
        with patch(
            "backend.app.adapters.claude_adapter.generate_text",
            return_value="claude answer",
        ) as claude, patch(
            "backend.app.adapters.gemini_adapter.generate_text",
            return_value="gemini answer",
        ) as gemini:
            self.assertEqual(ClaudeAdapter.generate("prompt"), "claude answer")
            self.assertEqual(GeminiAdapter.generate("prompt"), "gemini answer")

        self.assertEqual(claude.call_args.args[0], "Claude")
        self.assertEqual(gemini.call_args.args[0], "Gemini")

    def test_azure_requires_endpoint_and_api_version(self):
        with patch.object(
            __import__(
                "backend.app.adapters.azure_openai_adapter",
                fromlist=["settings"],
            ).settings,
            "AZURE_OPENAI_API_BASE",
            "",
        ), patch(
            "backend.app.adapters.azure_openai_adapter.generate_text"
        ) as generate:
            with self.assertRaisesRegex(RuntimeError, "API base and API version"):
                AzureOpenAIAdapter.generate("prompt")
        generate.assert_not_called()

    def test_provider_availability_requires_complete_configuration(self):
        settings = __import__(
            "backend.app.services.llm_router.health_monitor",
            fromlist=["settings"],
        ).settings
        with patch.object(settings, "AZURE_OPENAI_API_KEY", "configured"), patch.object(
            settings, "AZURE_OPENAI_API_BASE", ""
        ), patch.object(settings, "AZURE_OPENAI_API_VERSION", "v1"):
            status = HealthMonitor.get_provider_status("azure")

        self.assertFalse(status["available"])
        self.assertIn("AZURE_OPENAI_API_BASE", status["reason"])


if __name__ == "__main__":
    unittest.main()
