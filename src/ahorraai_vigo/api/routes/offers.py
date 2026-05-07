from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.api.deps import get_db_session, get_settings
from ahorraai_vigo.core.config import Settings
from ahorraai_vigo.modules.offers.schemas import OfferCard
from ahorraai_vigo.services.marketplace import MarketplaceService

router = APIRouter(prefix="/api/v1/offers", tags=["offers"])


@router.get("", response_model=list[OfferCard])
async def list_offers(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[OfferCard]:
    service = MarketplaceService(session)
    return await service.list_marketplace_offers(city_slug=settings.city_slug, limit=limit)
