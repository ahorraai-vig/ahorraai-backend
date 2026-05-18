from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.domain.enums import UserRole
from ahorraai_vigo.services.marketplace import MarketplaceService


async def seed_demo_data(session: AsyncSession) -> int:
    service = MarketplaceService(session)
    existing_offers = await service.list_marketplace_offers(limit=1)
    if existing_offers:
        return 0

    demo_businesses = [
        {
            "telegram_user_id": 910001,
            "username": "cafe_atlantico",
            "full_name": "Cafe Atlantico",
            "business_name": "Cafe Atlantico",
            "offers": [
                (
                    "Brunch mediterraneo",
                    "Cafe, zumo y tosta para media manana.",
                    Decimal("8.90"),
                ),
                (
                    "Desayuno rapido oficina",
                    "Cafe y croissant listos para recoger.",
                    Decimal("4.50"),
                ),
            ],
        },
        {
            "telegram_user_id": 910002,
            "username": "panaderia_ria",
            "full_name": "Panaderia Ria",
            "business_name": "Panaderia Ria",
            "offers": [
                (
                    "Pack desayuno",
                    "Cafe y bolleria recien hecha.",
                    Decimal("5.25"),
                ),
                (
                    "Empanada del dia",
                    "Racion individual lista para llevar.",
                    Decimal("3.80"),
                ),
            ],
        },
    ]

    created_offers = 0
    for demo_business in demo_businesses:
        owner = await service.ensure_user_from_telegram(
            telegram_user_id=demo_business["telegram_user_id"],
            username=demo_business["username"],
            full_name=demo_business["full_name"],
        )
        await service.set_user_role(user=owner, role=UserRole.BUSINESS)

        for title, description, price in demo_business["offers"]:
            await service.publish_offer_for_owner(
                owner=owner,
                business_name=demo_business["business_name"],
                title=title,
                description=description,
                price_amount=price,
            )
            created_offers += 1

    return created_offers
