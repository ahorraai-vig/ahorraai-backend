from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OfferCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    business_name: str
    title: str
    description: str
    price_amount: Decimal | None
    currency: str
    city_slug: str
    created_at: datetime
