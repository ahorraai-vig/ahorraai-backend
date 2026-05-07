from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ahorraai_vigo.bot.handlers.business import router as business_router
from ahorraai_vigo.bot.handlers.citizen import router as citizen_router
from ahorraai_vigo.bot.handlers.common import router as common_router
from ahorraai_vigo.bot.middlewares.context import AppContextMiddleware
from ahorraai_vigo.bot.middlewares.db import DbSessionMiddleware
from ahorraai_vigo.core.config import Settings


def build_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher(
    settings: Settings,
    session_maker: async_sessionmaker[AsyncSession],
) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(AppContextMiddleware(settings))
    dispatcher.update.outer_middleware(DbSessionMiddleware(session_maker))
    dispatcher.include_router(common_router)
    dispatcher.include_router(citizen_router)
    dispatcher.include_router(business_router)
    return dispatcher
