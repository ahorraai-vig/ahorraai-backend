from __future__ import annotations

import pytest

from ahorraai_vigo.core.config import Settings, validate_runtime_settings


def test_prod_settings_require_real_telegram_credentials() -> None:
    settings = Settings(
        _env_file=None,
        app_env="prod",
        database_url="sqlite+aiosqlite:///test.db",
        telegram_bot_token="123456:change_me",
        telegram_webhook_secret="change_me",
    )

    with pytest.raises(ValueError):
        validate_runtime_settings(settings)


def test_default_page_size_must_stay_in_safe_range() -> None:
    settings = Settings(_env_file=None, default_page_size=0)

    with pytest.raises(ValueError):
        validate_runtime_settings(settings)
