from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.domain.enums import DeliveryType, OrderStatus
from ahorraai_vigo.modules.orders.models import Order, OrderItem


class OrdersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        customer_user_id: UUID | None,
        business_id: UUID,
        total_amount: Decimal | None,
        currency: str,
        notes: str | None,
        metadata_json: dict[str, Any],
        delivery_type: str = DeliveryType.DELIVERY.value,
    ) -> Order:
        order = Order(
            customer_user_id=customer_user_id,
            business_id=business_id,
            status=OrderStatus.PENDING.value,
            total_amount=total_amount,
            currency=currency,
            delivery_type=delivery_type,
            notes=notes,
            metadata_json=metadata_json,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def add_item(
        self,
        *,
        order_id: UUID,
        title: str,
        quantity: Decimal,
        unit_price: Decimal | None,
        total_price: Decimal | None,
        metadata_json: dict[str, Any],
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            title=title,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            metadata_json=metadata_json,
        )
        self.session.add(item)
        await self.session.flush()
        return item
