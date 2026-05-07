from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.bot.keyboards import citizen_menu_keyboard
from ahorraai_vigo.bot.texts import EMPTY_OFFERS_TEXT
from ahorraai_vigo.services.marketplace import MarketplaceService

router = Router(name="citizen")


@router.message(Command("ofertas"))
async def list_offers_command(
    message: Message,
    db_session: AsyncSession,
) -> None:
    await _reply_with_offers(message, db_session)


@router.callback_query(F.data == "action:view_offers")
async def list_offers_callback(
    callback: CallbackQuery,
    db_session: AsyncSession,
) -> None:
    if callback.message is None:
        return

    await callback.answer()
    await _reply_with_offers(callback.message, db_session)


async def _reply_with_offers(message: Message, db_session: AsyncSession) -> None:
    service = MarketplaceService(db_session)
    offers = await service.list_marketplace_offers(limit=5)
    if not offers:
        await message.answer(EMPTY_OFFERS_TEXT, reply_markup=citizen_menu_keyboard())
        return

    lines = ["<b>Ofertas activas en Vigo</b>"]
    for index, offer in enumerate(offers, start=1):
        price = _format_price(offer.price_amount, offer.currency)
        lines.append(
            f"{index}. <b>{offer.title}</b>\n"
            f"Negocio: {offer.business_name}\n"
            f"Detalle: {offer.description}\n"
            f"Precio: {price}"
        )

    await message.answer("\n\n".join(lines), reply_markup=citizen_menu_keyboard())


def _format_price(price_amount: Decimal | None, currency: str) -> str:
    if price_amount is None:
        return "Consultar"
    return f"{price_amount} {currency}"
