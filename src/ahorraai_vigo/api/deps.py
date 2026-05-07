from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.core.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_maker = request.app.state.session_maker
    async with session_maker() as session:
        yield session
