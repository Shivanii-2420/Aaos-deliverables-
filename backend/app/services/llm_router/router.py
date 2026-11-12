from backend.app.adapters.azure_openai_adapter import AzureOpenAIAdapter
from backend.app.adapters.claude_adapter import ClaudeAdapter
from backend.app.adapters.gemini_adapter import GeminiAdapter
from backend.app.adapters.mock_adapter import MockAdapter


class LLMRouter:

    PROVIDERS = {
        "mock": MockAdapter,
        "azure": AzureOpenAIAdapter,
        "claude": ClaudeAdapter,
        "gemini": GeminiAdapter
    }

    @staticmethod
    def generate(provider: str, prompt: str):

        adapter = LLMRouter.PROVIDERS.get(provider)

        if not adapter:
            raise ValueError(f"Unsupported provider: {provider}")

        return adapter.generate(prompt)