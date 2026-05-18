from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        validate_default=True,
    )

    app_name: str = "AhorraAI"
    app_env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    city_slug: str = "vigo"
    default_page_size: int = 10
    db_auto_create: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ahorraai"

    telegram_bot_token: str = Field(default="123456:TEST_TOKEN", alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(default="", alias="TELEGRAM_WEBHOOK_SECRET")
    telegram_webhook_path: str = Field(default="/webhooks/telegram", alias="TELEGRAM_WEBHOOK_PATH")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    validate_runtime_settings(settings)
    return settings


def validate_runtime_settings(settings: Settings) -> None:
    if not settings.telegram_webhook_path.startswith("/"):
        raise ValueError("TELEGRAM_WEBHOOK_PATH must start with '/'.")

    if settings.default_page_size < 1 or settings.default_page_size > 100:
        raise ValueError("DEFAULT_PAGE_SIZE must be between 1 and 100.")

    if settings.app_env != "prod":
        return

    if settings.telegram_bot_token in {"", "123456:TEST_TOKEN", "123456:change_me"}:
        raise ValueError("Set a real TELEGRAM_BOT_TOKEN before running in prod.")

    if settings.telegram_webhook_secret in {"", "change_me"}:
        raise ValueError("Set a real TELEGRAM_WEBHOOK_SECRET before running in prod.")
