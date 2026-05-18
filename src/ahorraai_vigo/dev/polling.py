from __future__ import annotations

from ahorraai_vigo.bot.app import build_bot, build_dispatcher
from ahorraai_vigo.core.config import get_settings
from ahorraai_vigo.db.bootstrap import create_database_schema
from ahorraai_vigo.db.session import build_engine, build_session_maker


async def run_polling() -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url, echo=settings.app_env == "dev")
    session_maker = build_session_maker(engine)
    bot = build_bot(settings)
    dispatcher = build_dispatcher(settings, session_maker)

    if settings.db_auto_create:
        await create_database_schema(engine)

    await bot.delete_webhook(drop_pending_updates=False)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()
