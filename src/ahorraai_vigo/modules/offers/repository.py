from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ahorraai_vigo.domain.enums import OfferStatus
from ahorraai_vigo.modules.businesses.models import Business
from ahorraai_vigo.modules.offers.models import Offer


class OffersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        business_id: UUID,
        created_by_user_id: UUID | None,
        title: str,
        description: str,
        price_amount: Decimal | None,
        currency: str = "EUR",
    ) -> Offer:
        offer = Offer(
            business_id=business_id,
            created_by_user_id=created_by_user_id,
            title=title,
            description=description,
            price_amount=price_amount,
            currency=currency,
            status=OfferStatus.ACTIVE.value,
            visible_in_marketplace=True,
        )
        self.session.add(offer)
        await self.session.flush()
        return offer

    async def list_latest_active(self, *, city_slug: str, limit: int) -> list[Offer]:
        statement = (
            select(Offer)
            .join(Offer.business)
            .options(selectinload(Offer.business))
            .where(
                Offer.status == OfferStatus.ACTIVE.value,
                Offer.visible_in_marketplace.is_(True),
                Business.city_slug == city_slug,
            )
            .order_by(Offer.created_at.desc())
            .limit(limit)
        )
        result = await self.session.scalars(statement)
        return list(result.all())
