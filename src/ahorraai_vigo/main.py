from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ahorraai_vigo.api.routes.health import router as health_router
from ahorraai_vigo.api.routes.offers import router as offers_router
from ahorraai_vigo.api.routes.web import router as web_router
from ahorraai_vigo.api.routes.webhooks import router as webhooks_router
from ahorraai_vigo.bot.app import build_bot, build_dispatcher
from ahorraai_vigo.core.config import get_settings
from ahorraai_vigo.core.logging import configure_logging
from ahorraai_vigo.db.bootstrap import create_database_schema
from ahorraai_vigo.db.session import build_engine, build_session_maker


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    static_dir = Path(__file__).parent / "web" / "static"

    engine = build_engine(settings.database_url, echo=settings.app_env == "dev")
    session_maker = build_session_maker(engine)
    bot = build_bot(settings)
    dispatcher = build_dispatcher(settings, session_maker)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if settings.db_auto_create:
            await create_database_schema(engine)
        yield
        await bot.session.close()
        await engine.dispose()

    app = FastAPI(title=settings.app_name, version="0.3.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_maker = session_maker
    app.state.telegram_bot = bot
    app.state.telegram_dispatcher = dispatcher

    app.include_router(health_router)
    app.include_router(web_router)
    app.include_router(offers_router)
    app.include_router(webhooks_router)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    return app


app = create_app()
