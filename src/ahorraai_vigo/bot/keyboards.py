from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ahorraai_vigo.modules.offers.schemas import OfferCard


def role_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Soy ciudadano", callback_data="role:citizen")
    builder.button(text="Soy negocio", callback_data="role:business")
    builder.adjust(1)
    return builder.as_markup()


def citizen_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Buscar catalogo", callback_data="action:search_catalog")
    builder.button(text="Ver ofertas activas", callback_data="action:view_offers")
    builder.button(text="Ver mi lista", callback_data="action:view_cart")
    builder.button(text="Hacer pedido", callback_data="action:start_order")
    builder.adjust(1)
    return builder.as_markup()


def business_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Publicar oferta", callback_data="action:publish_offer")
    builder.adjust(1)
    return builder.as_markup()


def catalog_results_keyboard(offers: list[OfferCard]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for offer in offers:
        builder.button(
            text=f"Anadir {offer.title[:24]}",
            callback_data=f"cart:add:{offer.id}",
        )
    builder.button(text="Ver mi lista", callback_data="action:view_cart")
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard(*, has_items: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Buscar mas", callback_data="action:search_catalog")
    if has_items:
        builder.button(text="Hacer pedido", callback_data="action:start_order")
        builder.button(text="Limpiar lista", callback_data="cart:clear")
    builder.adjust(1)
    return builder.as_markup()


def order_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Confirmar pedido", callback_data="order:confirm")
    builder.button(text="Cancelar pedido", callback_data="order:cancel")
    builder.adjust(1)
    return builder.as_markup()
