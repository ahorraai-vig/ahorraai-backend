from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    CITIZEN = "citizen"
    BUSINESS = "business"


class OfferStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class DeliveryType(StrEnum):
    PICKUP = "pickup"
    DELIVERY = "delivery"
