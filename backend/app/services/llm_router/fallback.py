from backend.app.services.llm_router.health_monitor import HealthMonitor
from backend.app.services.llm_router.model_selector import ModelSelector
from backend.app.services.llm_router.router import LLMRouter


class FallbackRouter:

    @staticmethod
    def generate(prompt: str):

        available_providers = HealthMonitor.get_available_providers()
        selected_provider = ModelSelector.select_provider(
            available_providers,
            prompt
        )

        if not selected_provider:
            raise RuntimeError("No available provider could be selected.")

        try:
            content = LLMRouter.generate(selected_provider, prompt)

            return {
                "provider": selected_provider,
                "content": content
            }

        except Exception as ex:
            raise RuntimeError(
                f"LLM generation failed for {selected_provider}: {ex}"
            ) from ex
