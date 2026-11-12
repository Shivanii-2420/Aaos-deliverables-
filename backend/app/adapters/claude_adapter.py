from backend.app.adapters.litellm_client import generate_text
from backend.app.config.settings import settings


class ClaudeAdapter:

    MODEL = "claude-3-5-sonnet-latest"

    @staticmethod
    def generate(
        prompt: str
    ):
        return generate_text(
            "Claude",
            ClaudeAdapter.MODEL,
            prompt,
            settings.CLAUDE_API_KEY,
        )