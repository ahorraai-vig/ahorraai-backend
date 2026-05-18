from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.bot.keyboards import (
    cart_keyboard,
    catalog_results_keyboard,
    citizen_menu_keyboard,
    order_confirmation_keyboard,
)
from ahorraai_vigo.bot.states import DeliveryOrderStates, SearchCatalogStates
from ahorraai_vigo.bot.texts import (
    CART_EMPTY_TEXT,
    CATALOG_EMPTY_TEXT,
    CATALOG_SEARCH_PROMPT,
    EMPTY_OFFERS_TEXT,
    ORDER_ADDRESS_PROMPT,
    ORDER_CITY_PROMPT,
    ORDER_CREATED_TEXT,
    ORDER_NAME_PROMPT,
    ORDER_PHONE_PROMPT,
    ORDER_POSTAL_CODE_PROMPT,
)
from ahorraai_vigo.services.marketplace import MarketplaceService

router = Router(name="citizen")

CART_ITEMS_KEY = "cart_items"
ORDER_DRAFT_KEY = "order_draft"


@router.message(Command("ofertas"))
async def list_offers_command(message: Message, db_session: AsyncSession) -> None:
    await _reply_with_offers(message, db_session)


@router.message(Command("catalogo"))
async def search_catalog_command(message: Message, state: FSMContext) -> None:
    await _start_catalog_search(message, state)


@router.message(Command("lista"))
async def view_cart_command(message: Message, state: FSMContext) -> None:
    await _reply_with_cart(message, state)


@router.message(Command("pedido"))
async def start_order_command(message: Message, state: FSMContext) -> None:
    await _start_order_flow(message, state)


@router.callback_query(F.data == "action:view_offers")
async def list_offers_callback(callback: CallbackQuery, db_session: AsyncSession) -> None:
    if callback.message is None:
        return

    await callback.answer()
    await _reply_with_offers(callback.message, db_session)


@router.callback_query(F.data == "action:search_catalog")
async def search_catalog_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await callback.answer()
    await _start_catalog_search(callback.message, state)


@router.message(SearchCatalogStates.waiting_query)
async def receive_catalog_query(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    query = (message.text or "").strip()
    if not query:
        await message.answer(CATALOG_SEARCH_PROMPT)
        return

    service = MarketplaceService(db_session)
    offers = await service.search_marketplace_offers(query=query, limit=5)
    await state.set_state(None)
    if not offers:
        await message.answer(CATALOG_EMPTY_TEXT, reply_markup=citizen_menu_keyboard())
        return

    await message.answer(
        _format_offer_listing("Resultados del catalogo", offers),
        reply_markup=catalog_results_keyboard(offers),
    )


@router.callback_query(F.data.startswith("cart:add:"))
async def add_offer_to_cart(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    if callback.message is None or callback.data is None:
        return

    offer_id = UUID(callback.data.removeprefix("cart:add:"))
    service = MarketplaceService(db_session)
    offer = await service.get_offer_card(offer_id=offer_id)
    if offer is None:
        await callback.answer("La oferta ya no esta disponible.", show_alert=True)
        return

    cart_items = await _get_cart_items(state)
    if cart_items and any(item["business_id"] != str(offer.business_id) for item in cart_items):
        await callback.answer(
            "La lista solo puede mezclar ofertas del mismo negocio por ahora.",
            show_alert=True,
        )
        return

    for item in cart_items:
        if item["offer_id"] == str(offer.id):
            item["quantity"] += 1
            break
    else:
        cart_items.append(
            {
                "offer_id": str(offer.id),
                "business_id": str(offer.business_id),
                "business_name": offer.business_name,
                "title": offer.title,
                "price_amount": str(offer.price_amount) if offer.price_amount is not None else None,
                "currency": offer.currency,
                "quantity": 1,
            }
        )

    await _set_cart_items(state, cart_items)
    await callback.answer("Oferta anadida a tu lista.")
    await callback.message.answer(
        _format_cart_summary(cart_items),
        reply_markup=cart_keyboard(has_items=True),
    )


@router.callback_query(F.data == "action:view_cart")
async def view_cart_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await callback.answer()
    await _reply_with_cart(callback.message, state)


@router.callback_query(F.data == "cart:clear")
async def clear_cart_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await _set_cart_items(state, [])
    await callback.answer("Lista vaciada.")
    await callback.message.answer(CART_EMPTY_TEXT, reply_markup=cart_keyboard(has_items=False))


@router.callback_query(F.data == "action:start_order")
async def start_order_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await callback.answer()
    await _start_order_flow(callback.message, state)


@router.message(DeliveryOrderStates.waiting_contact_name)
async def capture_order_name(message: Message, state: FSMContext) -> None:
    await _update_order_draft(state, contact_name=(message.text or "").strip())
    await state.set_state(DeliveryOrderStates.waiting_contact_phone)
    await message.answer(ORDER_PHONE_PROMPT)


@router.message(DeliveryOrderStates.waiting_contact_phone)
async def capture_order_phone(message: Message, state: FSMContext) -> None:
    await _update_order_draft(state, contact_phone=(message.text or "").strip())
    await state.set_state(DeliveryOrderStates.waiting_delivery_address)
    await message.answer(ORDER_ADDRESS_PROMPT)


@router.message(DeliveryOrderStates.waiting_delivery_address)
async def capture_order_address(message: Message, state: FSMContext) -> None:
    await _update_order_draft(state, delivery_address=(message.text or "").strip())
    await state.set_state(DeliveryOrderStates.waiting_postal_code)
    await message.answer(ORDER_POSTAL_CODE_PROMPT)


@router.message(DeliveryOrderStates.waiting_postal_code)
async def capture_order_postal_code(message: Message, state: FSMContext) -> None:
    await _update_order_draft(state, postal_code=(message.text or "").strip())
    await state.set_state(DeliveryOrderStates.waiting_delivery_city)
    await message.answer(ORDER_CITY_PROMPT)


@router.message(DeliveryOrderStates.waiting_delivery_city)
async def capture_order_city(message: Message, state: FSMContext) -> None:
    await _update_order_draft(state, delivery_city=(message.text or "").strip())
    await state.set_state(None)
    cart_items = await _get_cart_items(state)
    draft = await _get_order_draft(state)
    await message.answer(
        _format_order_preview(cart_items, draft),
        reply_markup=order_confirmation_keyboard(),
    )


@router.callback_query(F.data == "order:confirm")
async def confirm_order_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    if callback.message is None or callback.from_user is None:
        return

    cart_items = await _get_cart_items(state)
    draft = await _get_order_draft(state)
    if not cart_items or not draft:
        await callback.answer("No hay un pedido listo para confirmar.", show_alert=True)
        return

    service = MarketplaceService(db_session)
    customer = await service.ensure_user_from_telegram(
        telegram_user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )

    try:
        order = await service.create_order_from_offer_cart(
            customer=customer,
            contact_name=draft["contact_name"],
            contact_phone=draft["contact_phone"],
            delivery_address=draft["delivery_address"],
            postal_code=draft["postal_code"],
            delivery_city=draft["delivery_city"],
            cart_items=cart_items,
        )
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    total_amount = order.total_amount if order.total_amount is not None else "Consultar"
    business_name = str(order.metadata_json.get("business_name", "Negocio"))
    await _clear_order_draft(state)
    await _set_cart_items(state, [])
    await callback.answer("Pedido confirmado.")
    await callback.message.answer(
        ORDER_CREATED_TEXT.format(
            order_id=order.id,
            business_name=business_name,
            total_amount=total_amount,
        ),
        reply_markup=citizen_menu_keyboard(),
    )


@router.callback_query(F.data == "order:cancel")
async def cancel_order_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    await _clear_order_draft(state)
    await state.set_state(None)
    await callback.answer("Pedido cancelado.")
    await callback.message.answer("El pedido se cancelo y tu lista sigue guardada.")


async def _start_catalog_search(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchCatalogStates.waiting_query)
    await message.answer(CATALOG_SEARCH_PROMPT)


async def _reply_with_offers(message: Message, db_session: AsyncSession) -> None:
    service = MarketplaceService(db_session)
    offers = await service.list_marketplace_offers(limit=5)
    if not offers:
        await message.answer(EMPTY_OFFERS_TEXT, reply_markup=citizen_menu_keyboard())
        return

    await message.answer(
        _format_offer_listing("Ofertas activas en Vigo", offers),
        reply_markup=catalog_results_keyboard(offers),
    )


async def _reply_with_cart(message: Message, state: FSMContext) -> None:
    cart_items = await _get_cart_items(state)
    if not cart_items:
        await message.answer(CART_EMPTY_TEXT, reply_markup=cart_keyboard(has_items=False))
        return

    await message.answer(
        _format_cart_summary(cart_items),
        reply_markup=cart_keyboard(has_items=True),
    )


async def _start_order_flow(message: Message, state: FSMContext) -> None:
    cart_items = await _get_cart_items(state)
    if not cart_items:
        await message.answer(CART_EMPTY_TEXT, reply_markup=cart_keyboard(has_items=False))
        return

    await state.set_state(DeliveryOrderStates.waiting_contact_name)
    await _clear_order_draft(state)
    await message.answer(
        _format_cart_summary(cart_items),
        reply_markup=cart_keyboard(has_items=True),
    )
    await message.answer(ORDER_NAME_PROMPT)


def _format_offer_listing(title: str, offers: list) -> str:
    lines = [f"<b>{title}</b>"]
    for index, offer in enumerate(offers, start=1):
        lines.append(
            f"{index}. <b>{offer.title}</b>\n"
            f"Negocio: {offer.business_name}\n"
            f"Detalle: {offer.description}\n"
            f"Precio: {_format_price(offer.price_amount, offer.currency)}"
        )
    return "\n\n".join(lines)


def _format_cart_summary(cart_items: list[dict[str, str | int | None]]) -> str:
    total_amount = Decimal("0.00")
    currency = "EUR"
    lines = ["<b>Tu lista actual</b>"]
    for index, item in enumerate(cart_items, start=1):
        price_amount = item["price_amount"]
        quantity = int(item["quantity"])
        unit_price = Decimal(price_amount) if isinstance(price_amount, str) else None
        subtotal = unit_price * quantity if unit_price is not None else None
        currency = str(item["currency"])
        if subtotal is not None:
            total_amount += subtotal

        lines.append(
            f"{index}. <b>{item['title']}</b>\n"
            f"Negocio: {item['business_name']}\n"
            f"Cantidad: {quantity}\n"
            f"Subtotal: {_format_price(subtotal, currency)}"
        )

    lines.append(f"Total estimado: <b>{_format_price(total_amount, currency)}</b>")
    return "\n\n".join(lines)


def _format_order_preview(
    cart_items: list[dict[str, str | int | None]],
    draft: dict[str, str],
) -> str:
    return (
        f"{_format_cart_summary(cart_items)}\n\n"
        "<b>Entrega</b>\n"
        f"Nombre: {draft['contact_name']}\n"
        f"Telefono: {draft['contact_phone']}\n"
        f"Direccion: {draft['delivery_address']}\n"
        f"Codigo postal: {draft['postal_code']}\n"
        f"Ciudad: {draft['delivery_city']}\n\n"
        "Pulsa confirmar para guardar el pedido."
    )


def _format_price(price_amount: Decimal | None, currency: str) -> str:
    if price_amount is None:
        return "Consultar"
    return f"{price_amount} {currency}"


async def _get_cart_items(state: FSMContext) -> list[dict[str, str | int | None]]:
    data = await state.get_data()
    return list(data.get(CART_ITEMS_KEY, []))


async def _set_cart_items(state: FSMContext, cart_items: list[dict[str, str | int | None]]) -> None:
    data = await state.get_data()
    data[CART_ITEMS_KEY] = cart_items
    await state.set_data(data)


async def _get_order_draft(state: FSMContext) -> dict[str, str]:
    data = await state.get_data()
    return dict(data.get(ORDER_DRAFT_KEY, {}))


async def _update_order_draft(state: FSMContext, **values: str) -> None:
    data = await state.get_data()
    draft = dict(data.get(ORDER_DRAFT_KEY, {}))
    draft.update(values)
    data[ORDER_DRAFT_KEY] = draft
    await state.set_data(data)


async def _clear_order_draft(state: FSMContext) -> None:
    data = await state.get_data()
    data.pop(ORDER_DRAFT_KEY, None)
    await state.set_data(data)
