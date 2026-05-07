from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.domain.enums import UserRole
from ahorraai_vigo.modules.businesses.models import Business
from ahorraai_vigo.modules.businesses.repository import BusinessesRepository
from ahorraai_vigo.modules.offers.models import Offer
from ahorraai_vigo.modules.offers.repository import OffersRepository
from ahorraai_vigo.modules.offers.schemas import OfferCard
from ahorraai_vigo.modules.users.models import AppUser
from ahorraai_vigo.modules.users.repository import UsersRepository


class MarketplaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UsersRepository(session)
        self.businesses = BusinessesRepository(session)
        self.offers = OffersRepository(session)

    async def ensure_user_from_telegram(
        self,
        *,
        telegram_user_id: int,
        username: str | None,
        full_name: str | None,
    ) -> AppUser:
        user = await self.users.upsert_telegram_user(
            telegram_user_id=telegram_user_id,
            username=username,
            full_name=full_name,
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_user_role(self, *, user: AppUser, role: UserRole) -> AppUser:
        user.role = role.value
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def publish_offer_for_owner(
        self,
        *,
        owner: AppUser,
        business_name: str,
        title: str,
        description: str,
        price_amount: Decimal | None,
        city_slug: str = "vigo",
    ) -> tuple[Business, Offer]:
        business = await self.businesses.get_by_owner_user_id(owner.id)
        if business is None:
            business = await self.businesses.create(
                owner_user_id=owner.id,
                name=business_name,
                city_slug=city_slug,
            )
        else:
            business.name = business_name
            business.city_slug = city_slug

        offer = await self.offers.create(
            business_id=business.id,
            created_by_user_id=owner.id,
            title=title,
            description=description,
            price_amount=price_amount,
        )
        await self.session.commit()
        await self.session.refresh(business)
        await self.session.refresh(offer)
        return business, offer

    async def list_marketplace_offers(
        self,
        *,
        city_slug: str = "vigo",
        limit: int = 10,
    ) -> list[OfferCard]:
        offers = await self.offers.list_latest_active(city_slug=city_slug, limit=limit)
        return [
            OfferCard(
                id=offer.id,
                business_name=offer.business.name,
                title=offer.title,
                description=offer.description,
                price_amount=offer.price_amount,
                currency=offer.currency,
                city_slug=offer.business.city_slug,
                created_at=offer.created_at,
            )
            for offer in offers
        ]
