from __future__ import annotations

from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.bot.keyboards import business_menu_keyboard
from ahorraai_vigo.bot.states import PublishOfferStates
from ahorraai_vigo.bot.texts import (
    BUSINESS_DESCRIPTION_PROMPT,
    BUSINESS_NAME_PROMPT,
    BUSINESS_PRICE_PROMPT,
    BUSINESS_PUBLISH_SUCCESS_TEXT,
    BUSINESS_TITLE_PROMPT,
    INVALID_PRICE_TEXT,
)
from ahorraai_vigo.services.marketplace import MarketplaceService

router = Router(name="business")


@router.message(Command("publicar"))
async def start_publish_command(message: Message, state: FSMContext) -> None:
    await _start_publish_flow(message, state)


@router.callback_query(F.data == "action:publish_offer")
async def start_publish_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await callback.answer()
    await _start_publish_flow(callback.message, state)


@router.message(PublishOfferStates.waiting_business_name)
async def capture_business_name(message: Message, state: FSMContext) -> None:
    business_name = (message.text or "").strip()
    if not business_name:
        await message.answer(BUSINESS_NAME_PROMPT)
        return

    await state.update_data(business_name=business_name)
    await state.set_state(PublishOfferStates.waiting_offer_title)
    await message.answer(BUSINESS_TITLE_PROMPT)


@router.message(PublishOfferStates.waiting_offer_title)
async def capture_offer_title(message: Message, state: FSMContext) -> None:
    offer_title = (message.text or "").strip()
    if not offer_title:
        await message.answer(BUSINESS_TITLE_PROMPT)
        return

    await state.update_data(offer_title=offer_title)
    await state.set_state(PublishOfferStates.waiting_offer_description)
    await message.answer(BUSINESS_DESCRIPTION_PROMPT)


@router.message(PublishOfferStates.waiting_offer_description)
async def capture_offer_description(message: Message, state: FSMContext) -> None:
    offer_description = (message.text or "").strip()
    if not offer_description:
        await message.answer(BUSINESS_DESCRIPTION_PROMPT)
        return

    await state.update_data(offer_description=offer_description)
    await state.set_state(PublishOfferStates.waiting_offer_price)
    await message.answer(BUSINESS_PRICE_PROMPT)


@router.message(PublishOfferStates.waiting_offer_price)
async def capture_offer_price(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    if message.from_user is None:
        return

    price = _parse_price((message.text or "").strip())
    if price == "invalid":
        await message.answer(INVALID_PRICE_TEXT)
        return

    form_data = await state.get_data()
    service = MarketplaceService(db_session)
    user = await service.ensure_user_from_telegram(
        telegram_user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    business, offer = await service.publish_offer_for_owner(
        owner=user,
        business_name=form_data["business_name"],
        title=form_data["offer_title"],
        description=form_data["offer_description"],
        price_amount=price,
    )

    await state.clear()
    summary = BUSINESS_PUBLISH_SUCCESS_TEXT.format(
        business_name=business.name,
        offer_title=offer.title,
    )
    await message.answer(summary, reply_markup=business_menu_keyboard())


async def _start_publish_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(PublishOfferStates.waiting_business_name)
    await message.answer(BUSINESS_NAME_PROMPT)


def _parse_price(raw_value: str) -> Decimal | None | str:
    normalized = raw_value.strip().lower().replace("€", "").replace(",", ".")
    if normalized in {"", "sin precio", "consultar", "no", "n/a"}:
        return None

    try:
        return Decimal(normalized).quantize(Decimal("0.01"))
    except InvalidOperation:
        return "invalid"
