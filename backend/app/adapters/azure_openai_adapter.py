from backend.app.adapters.litellm_client import generate_text
from backend.app.config.settings import settings


class AzureOpenAIAdapter:

    # Azure uses deployment name via LiteLLM format
    MODEL = "azure/gpt-4o-mini"

    @staticmethod
    def generate(prompt: str):
        # Prefer deployment name when provided by env (common Azure setup)
        model = AzureOpenAIAdapter.MODEL
        if getattr(settings, "AZURE_OPENAI_DEPLOYMENT_NAME", None):
            # litellm/Azure expects deployment name as model or prefixed by 'azure/'
            model = f"azure/{settings.AZURE_OPENAI_DEPLOYMENT_NAME}"

        api_base = settings.AZURE_OPENAI_API_BASE or None
        api_version = settings.AZURE_OPENAI_API_VERSION or None
        if not api_base or not api_version:
            raise RuntimeError(
                "Azure OpenAI API base and API version must be configured."
            )

        return generate_text(
            "Azure OpenAI",
            model,
            prompt,
            settings.AZURE_OPENAI_API_KEY,
            api_base=api_base,
            api_version=api_version,
        )