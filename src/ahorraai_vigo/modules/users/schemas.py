from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TelegramUserIdentity:
    telegram_user_id: int
    username: str | None = None
    full_name: str | None = None
