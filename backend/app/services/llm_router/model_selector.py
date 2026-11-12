from backend.app.services.llm_router.health_monitor import HealthMonitor
from backend.app.config.settings import settings


class ModelSelector:

    PREFERRED_ORDER = ["mock", "azure", "claude", "gemini"]

    @staticmethod
    def select_provider(
        available_providers: list[str],
        prompt: str
    ) -> str | None:

        if not available_providers:
            return None

        prompt_lower = prompt.lower()

        configured_default = settings.DEFAULT_LLM_PROVIDER.lower()
        if configured_default in available_providers:
            return configured_default

        if "secure" in prompt_lower or "confidential" in prompt_lower:
            if "azure" in available_providers:
                return "azure"

        preference = [
            provider
            for provider in ModelSelector.PREFERRED_ORDER
            if provider in available_providers
        ]

        if preference:
            return preference[0]

        return available_providers[0]

    @staticmethod
    def select_provider_by_prompt(
        available_providers: list[str],
        prompt: str
    ) -> str | None:

        return ModelSelector.select_provider(
            available_providers,
            prompt
        )
