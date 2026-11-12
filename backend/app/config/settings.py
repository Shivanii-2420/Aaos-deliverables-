from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv
from pydantic import field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "aaos_local.db"

# Load backend/.env into environment variables before instantiating Settings.
project_root = Path(__file__).resolve().parents[2]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=False)


class Settings(BaseSettings):

    APP_NAME: str = "AAOS"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
    REDIS_URL: str = ""
    DEFAULT_LLM_PROVIDER: str = "mock"

    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_BASE: str = ""
    AZURE_OPENAI_API_VERSION: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = ""

    CLAUDE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    API_TOKEN: str = ""
    DEEPEVAL_JUDGE_MODEL: str = ""
    DEEPEVAL_ALLOW_JUDGE_CALLS: bool = False

    @field_validator("API_TOKEN")
    @classmethod
    def validate_api_token(cls, value: str) -> str:
        if value and len(value) < 24:
            raise ValueError("API_TOKEN must contain at least 24 characters")
        return value

    model_config = SettingsConfigDict(
        env_file=str(env_path) if env_path.exists() else ".env",
        extra="ignore"
    )


settings = Settings()