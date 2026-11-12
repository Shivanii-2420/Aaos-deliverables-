from backend.app.config.settings import settings
from backend.app.services.llm_router.router import LLMRouter


class HealthMonitor:

    PROVIDER_CONFIG = {
        "mock": {
            "api_key": None,
            "required": False,
            "preferred": True
        },
        "azure": {
            "api_key": "AZURE_OPENAI_API_KEY",
            "required_settings": (
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_API_BASE",
                "AZURE_OPENAI_API_VERSION",
            ),
            "required": True,
            "preferred": True
        },
        "claude": {
            "api_key": "CLAUDE_API_KEY",
            "required_settings": ("CLAUDE_API_KEY",),
            "required": False,
            "preferred": False
        },
        "gemini": {
            "api_key": "GEMINI_API_KEY",
            "required_settings": ("GEMINI_API_KEY",),
            "required": False,
            "preferred": False
        }
    }

    @staticmethod
    def get_provider_status(provider: str) -> dict:
        config = HealthMonitor.PROVIDER_CONFIG.get(provider, {})
        api_key_name = config.get("api_key")
        required_settings = config.get("required_settings", ())
        missing_settings = [
            name for name in required_settings
            if not getattr(settings, name, None)
        ]
        available = provider == "mock" or not missing_settings
        reason = (
            "Local deterministic provider"
            if provider == "mock"
            else "Configured; live health is not checked" if available
            else f"Missing configuration: {', '.join(missing_settings)}"
        )

        return {
            "provider": provider,
            "available": available,
            "required": config.get("required", False),
            "preferred": config.get("preferred", False),
            "reason": reason,
            "api_key_name": api_key_name,
            "uptime": None,
            "latency_ms": None
        }

    @staticmethod
    def get_all_provider_statuses() -> list[dict]:
        return [
            HealthMonitor.get_provider_status(provider)
            for provider in LLMRouter.PROVIDERS
        ]

    @staticmethod
    def get_available_providers() -> list[str]:
        return [
            status["provider"]
            for status in HealthMonitor.get_all_provider_statuses()
            if status["available"]
        ]

    @staticmethod
    def get_provider_graph() -> dict:
        statuses = HealthMonitor.get_all_provider_statuses()
        return {
            "providers": [status["provider"] for status in statuses],
            "availability": {
                status["provider"]: status["available"]
                for status in statuses
            },
            "meta": {
                "generated_by": "HealthMonitor",
                "description": "Basic provider health graph"
            }
        }
