from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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

    @field_validator("telegram_webhook_path")
    @classmethod
    def validate_webhook_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("TELEGRAM_WEBHOOK_PATH must start with '/'.")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
