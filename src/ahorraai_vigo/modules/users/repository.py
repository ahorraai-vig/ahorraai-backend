from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.modules.users.models import AppUser


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> AppUser | None:
        statement = select(AppUser).where(AppUser.telegram_user_id == telegram_user_id)
        return await self.session.scalar(statement)

    async def upsert_telegram_user(
        self,
        *,
        telegram_user_id: int,
        username: str | None,
        full_name: str | None,
    ) -> AppUser:
        user = await self.get_by_telegram_user_id(telegram_user_id)
        if user is None:
            user = AppUser(
                telegram_user_id=telegram_user_id,
                username=username,
                full_name=full_name,
            )
            self.session.add(user)
        else:
            user.username = username
            user.full_name = full_name

        await self.session.flush()
        return user
