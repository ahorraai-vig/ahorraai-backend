from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class CreateBusinessPayload:
    owner_user_id: UUID
    name: str
    city_slug: str = "vigo"
