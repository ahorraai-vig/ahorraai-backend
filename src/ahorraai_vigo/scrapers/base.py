from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class ScrapedItem:
    external_id: str
    entity_type: str
    title: str
    source_name: str
    source_url: str
    city_slug: str = "vigo"
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScraperRunSummary:
    source_name: str
    items_seen: int
    items_created: int
    items_updated: int


class BaseScraper(Protocol):
    name: str

    async def collect(self) -> list[ScrapedItem]:
        """Return normalized records from one local source."""
