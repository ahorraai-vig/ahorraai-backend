from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def role_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Soy ciudadano", callback_data="role:citizen")
    builder.button(text="Soy negocio", callback_data="role:business")
    builder.adjust(1)
    return builder.as_markup()


def citizen_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Ver ofertas activas", callback_data="action:view_offers")
    builder.adjust(1)
    return builder.as_markup()


def business_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Publicar oferta", callback_data="action:publish_offer")
    builder.adjust(1)
    return builder.as_markup()
