import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_name: str = "DANEM Sales Copilot API"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./danem_sales_copilot.db")
    internet_enrichment_mode: str = os.getenv("INTERNET_ENRICHMENT_MODE", "OFF")  # OFF | WHITELIST | FULL

    openai_enabled: bool = _env_bool("OPENAI_ENABLED", False)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    ai_mode: str = os.getenv("AI_MODE", "hybrid")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "10"))


settings = Settings()
