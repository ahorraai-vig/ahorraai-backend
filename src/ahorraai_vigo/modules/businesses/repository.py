from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.modules.businesses.models import Business


class BusinessesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_owner_user_id(self, owner_user_id: UUID) -> Business | None:
        statement = select(Business).where(Business.owner_user_id == owner_user_id)
        return await self.session.scalar(statement)

    async def create(
        self,
        *,
        owner_user_id: UUID,
        name: str,
        city_slug: str,
    ) -> Business:
        business = Business(
            owner_user_id=owner_user_id,
            name=name,
            city_slug=city_slug,
        )
        self.session.add(business)
        await self.session.flush()
        return business
