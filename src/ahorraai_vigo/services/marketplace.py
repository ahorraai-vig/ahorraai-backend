from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.domain.enums import DeliveryType, UserRole
from ahorraai_vigo.modules.businesses.models import Business
from ahorraai_vigo.modules.businesses.repository import BusinessesRepository
from ahorraai_vigo.modules.offers.models import Offer
from ahorraai_vigo.modules.offers.repository import OffersRepository
from ahorraai_vigo.modules.offers.schemas import OfferCard
from ahorraai_vigo.modules.orders.models import Order
from ahorraai_vigo.modules.orders.repository import OrdersRepository
from ahorraai_vigo.modules.users.models import AppUser
from ahorraai_vigo.modules.users.repository import UsersRepository


class MarketplaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UsersRepository(session)
        self.businesses = BusinessesRepository(session)
        self.offers = OffersRepository(session)
        self.orders = OrdersRepository(session)

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
                business_id=offer.business_id,
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

    async def search_marketplace_offers(
        self,
        *,
        query: str,
        city_slug: str = "vigo",
        limit: int = 10,
    ) -> list[OfferCard]:
        offers = await self.offers.search_active(city_slug=city_slug, query=query, limit=limit)
        return [
            OfferCard(
                id=offer.id,
                business_id=offer.business_id,
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

    async def get_offer_card(self, *, offer_id: UUID) -> OfferCard | None:
        offer = await self.offers.get_active_by_id(offer_id=offer_id)
        if offer is None:
            return None

        return OfferCard(
            id=offer.id,
            business_id=offer.business_id,
            business_name=offer.business.name,
            title=offer.title,
            description=offer.description,
            price_amount=offer.price_amount,
            currency=offer.currency,
            city_slug=offer.business.city_slug,
            created_at=offer.created_at,
        )

    async def create_order_from_offer_cart(
        self,
        *,
        customer: AppUser,
        contact_name: str,
        contact_phone: str,
        delivery_address: str,
        postal_code: str,
        delivery_city: str,
        cart_items: list[dict[str, str | int]],
    ) -> Order:
        offer_ids = [UUID(str(item["offer_id"])) for item in cart_items]
        offers = await self.offers.get_active_by_ids(offer_ids=offer_ids)
        offers_by_id = {offer.id: offer for offer in offers}

        if len(offers_by_id) != len(offer_ids):
            raise ValueError("Some cart items are no longer available.")

        first_offer = offers[0]
        business_id = first_offer.business_id
        business_name = first_offer.business.name
        currency = first_offer.currency
        total_amount = Decimal("0.00")
        normalized_items: list[tuple[Offer, Decimal]] = []

        for raw_item in cart_items:
            offer = offers_by_id[UUID(str(raw_item["offer_id"]))]
            quantity = Decimal(str(raw_item["quantity"]))
            if offer.business_id != business_id:
                raise ValueError("Cart items must belong to the same business.")

            normalized_items.append((offer, quantity))
            if offer.price_amount is not None:
                total_amount += offer.price_amount * quantity

        order = await self.orders.create(
            customer_user_id=customer.id,
            business_id=business_id,
            total_amount=total_amount,
            currency=currency,
            notes=(
                f"Delivery order for {contact_name}. "
                "Phone: "
                f"{contact_phone}. Address: {delivery_address}, "
                f"{postal_code}, {delivery_city}."
            ),
            metadata_json={
                "contact_name": contact_name,
                "contact_phone": contact_phone,
                "delivery_address": delivery_address,
                "postal_code": postal_code,
                "delivery_city": delivery_city,
                "business_name": business_name,
            },
            delivery_type=DeliveryType.DELIVERY.value,
        )

        for offer, quantity in normalized_items:
            unit_price = offer.price_amount
            total_price = unit_price * quantity if unit_price is not None else None
            await self.orders.add_item(
                order_id=order.id,
                title=offer.title,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                metadata_json={
                    "offer_id": str(offer.id),
                    "business_id": str(offer.business_id),
                    "business_name": offer.business.name,
                    "description": offer.description,
                },
            )

        await self.session.commit()
        await self.session.refresh(order)
        return order
