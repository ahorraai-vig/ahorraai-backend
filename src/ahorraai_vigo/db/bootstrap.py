from __future__ import annotations

from importlib import import_module

from sqlalchemy.ext.asyncio import AsyncEngine

from ahorraai_vigo.db.base import Base


def load_models() -> None:
    for module_name in (
        "ahorraai_vigo.modules.users.models",
        "ahorraai_vigo.modules.businesses.models",
        "ahorraai_vigo.modules.offers.models",
    ):
        import_module(module_name)


async def create_database_schema(engine: AsyncEngine) -> None:
    load_models()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
