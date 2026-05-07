from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ahorraai_vigo.db.base import Base

if TYPE_CHECKING:
    from ahorraai_vigo.modules.offers.models import Offer
    from ahorraai_vigo.modules.users.models import AppUser


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(ForeignKey("app_users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str | None] = mapped_column(String(180), nullable=True)
    business_type: Mapped[str] = mapped_column(String(40), default="local_business")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    city_slug: Mapped[str] = mapped_column(String(80), default="vigo")
    neighborhood: Mapped[str | None] = mapped_column(String(120), nullable=True)
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

    owner: Mapped[AppUser] = relationship(back_populates="businesses")
    offers: Mapped[list[Offer]] = relationship(
        back_populates="business",
        cascade="all, delete-orphan",
    )
