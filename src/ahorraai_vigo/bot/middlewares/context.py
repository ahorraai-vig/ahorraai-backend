from __future__ import annotations

from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from ahorraai_vigo.core.config import Settings


class AppContextMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def __call__(self, handler: Any, event: TelegramObject, data: dict[str, Any]) -> Any:
        data["settings"] = self.settings
        return await handler(event, data)
