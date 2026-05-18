from __future__ import annotations

import asyncio

from ahorraai_vigo.core.config import get_settings
from ahorraai_vigo.db.bootstrap import create_database_schema
from ahorraai_vigo.db.session import build_engine, build_session_maker
from ahorraai_vigo.dev.seed_demo import seed_demo_data


async def main() -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url, echo=settings.app_env == "dev")
    session_maker = build_session_maker(engine)

    await create_database_schema(engine)

    async with session_maker() as session:
        created = await seed_demo_data(session)

    await engine.dispose()
    print(f"seeded={created}")


if __name__ == "__main__":
    asyncio.run(main())
