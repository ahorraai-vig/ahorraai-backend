from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.domain.enums import UserRole
from ahorraai_vigo.modules.orders.models import Order, OrderItem
from ahorraai_vigo.services.marketplace import MarketplaceService


@pytest.mark.asyncio
async def test_business_offer_becomes_visible_in_marketplace(db_session: AsyncSession) -> None:
    service = MarketplaceService(db_session)

    business_user = await service.ensure_user_from_telegram(
        telegram_user_id=1001,
        username="negocio_vigo",
        full_name="Negocio Vigo",
    )
    await service.set_user_role(user=business_user, role=UserRole.BUSINESS)

    business, offer = await service.publish_offer_for_owner(
        owner=business_user,
        business_name="Panaderia Atlantico",
        title="Desayuno completo",
        description="Cafe y croissant a precio especial hasta las 12:00.",
        price_amount=Decimal("4.50"),
    )

    citizen_user = await service.ensure_user_from_telegram(
        telegram_user_id=2002,
        username="cliente_vigo",
        full_name="Cliente Vigo",
    )
    await service.set_user_role(user=citizen_user, role=UserRole.CITIZEN)

    offers = await service.list_marketplace_offers(city_slug="vigo", limit=10)

    assert business.name == "Panaderia Atlantico"
    assert offer.title == "Desayuno completo"
    assert len(offers) == 1
    assert offers[0].business_name == "Panaderia Atlantico"
    assert offers[0].title == "Desayuno completo"
    assert offers[0].price_amount == Decimal("4.50")


@pytest.mark.asyncio
async def test_user_role_can_be_updated(db_session: AsyncSession) -> None:
    service = MarketplaceService(db_session)

    user = await service.ensure_user_from_telegram(
        telegram_user_id=3003,
        username="oscar",
        full_name="Oscar",
    )
    updated_user = await service.set_user_role(user=user, role=UserRole.BUSINESS)

    assert updated_user.role == UserRole.BUSINESS.value


@pytest.mark.asyncio
async def test_marketplace_search_returns_matching_offer(db_session: AsyncSession) -> None:
    service = MarketplaceService(db_session)

    business_user = await service.ensure_user_from_telegram(
        telegram_user_id=4004,
        username="cafeteria_vigo",
        full_name="Cafeteria Vigo",
    )
    await service.set_user_role(user=business_user, role=UserRole.BUSINESS)
    await service.publish_offer_for_owner(
        owner=business_user,
        business_name="Cafe Atlantico",
        title="Brunch mediterraneo",
        description="Cafe, zumo y tosta para media manana.",
        price_amount=Decimal("8.90"),
    )

    results = await service.search_marketplace_offers(query="brunch", city_slug="vigo", limit=5)

    assert len(results) == 1
    assert results[0].business_name == "Cafe Atlantico"
    assert results[0].title == "Brunch mediterraneo"


@pytest.mark.asyncio
async def test_order_from_cart_persists_order_and_items(db_session: AsyncSession) -> None:
    service = MarketplaceService(db_session)

    business_user = await service.ensure_user_from_telegram(
        telegram_user_id=5005,
        username="panaderia_vigo",
        full_name="Panaderia Vigo",
    )
    await service.set_user_role(user=business_user, role=UserRole.BUSINESS)
    business, offer = await service.publish_offer_for_owner(
        owner=business_user,
        business_name="Panaderia Ria",
        title="Pack desayuno",
        description="Cafe y bolleria recien hecha.",
        price_amount=Decimal("5.25"),
    )

    customer = await service.ensure_user_from_telegram(
        telegram_user_id=6006,
        username="cliente_portfolio",
        full_name="Cliente Portfolio",
    )
    await service.set_user_role(user=customer, role=UserRole.CITIZEN)

    order = await service.create_order_from_offer_cart(
        customer=customer,
        contact_name="Oscar",
        contact_phone="600123123",
        delivery_address="Rua del Puerto 12",
        postal_code="36202",
        delivery_city="Vigo",
        cart_items=[{"offer_id": str(offer.id), "quantity": 2}],
    )

    stored_order = await db_session.scalar(select(Order).where(Order.id == order.id))
    stored_items = list(
        (
            await db_session.scalars(select(OrderItem).where(OrderItem.order_id == order.id))
        ).all()
    )

    assert stored_order is not None
    assert stored_order.business_id == business.id
    assert stored_order.customer_user_id == customer.id
    assert stored_order.total_amount == Decimal("10.50")
    assert stored_order.metadata_json["delivery_city"] == "Vigo"
    assert len(stored_items) == 1
    assert stored_items[0].title == "Pack desayuno"
    assert stored_items[0].quantity == Decimal("2")
    assert stored_items[0].total_price == Decimal("10.50")
