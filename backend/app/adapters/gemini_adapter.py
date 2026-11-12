from backend.app.adapters.litellm_client import generate_text
from backend.app.config.settings import settings


class GeminiAdapter:

    MODEL = "gemini-2.5-flash"

    @staticmethod
    def generate(prompt: str):
        return generate_text(
            "Gemini",
            GeminiAdapter.MODEL,
            prompt,
            settings.GEMINI_API_KEY,
        )