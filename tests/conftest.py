from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ahorraai_vigo.db.bootstrap import create_database_schema


@pytest.fixture
async def db_session() -> AsyncSession:
    temp_dir = Path(".tmp") / "tests"
    temp_dir.mkdir(parents=True, exist_ok=True)
    database_path = (temp_dir / f"{uuid4().hex}.db").resolve()
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path.as_posix()}")
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    await create_database_schema(engine)

    async with session_maker() as session:
        yield session

    await engine.dispose()
    database_path.unlink(missing_ok=True)
