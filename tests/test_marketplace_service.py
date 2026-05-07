from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.domain.enums import UserRole
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
