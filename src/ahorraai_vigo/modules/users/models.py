from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ahorraai_vigo.db.base import Base
from ahorraai_vigo.domain.enums import UserRole

if TYPE_CHECKING:
    from ahorraai_vigo.modules.businesses.models import Business
    from ahorraai_vigo.modules.offers.models import Offer


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.CITIZEN.value)
    city_slug: Mapped[str] = mapped_column(String(80), default="vigo")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    businesses: Mapped[list[Business]] = relationship(back_populates="owner")
    created_offers: Mapped[list[Offer]] = relationship(back_populates="created_by")
