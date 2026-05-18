from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ahorraai_vigo.bot.keyboards import business_menu_keyboard, citizen_menu_keyboard, role_keyboard
from ahorraai_vigo.bot.states import PublishOfferStates
from ahorraai_vigo.bot.texts import (
    BUSINESS_NAME_PROMPT,
    BUSINESS_WELCOME_TEXT,
    CITIZEN_WELCOME_TEXT,
    START_TEXT,
)
from ahorraai_vigo.domain.enums import UserRole
from ahorraai_vigo.services.marketplace import MarketplaceService

router = Router(name="common")


@router.message(CommandStart())
@router.message(Command("menu"))
async def start_command(
    message: Message,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    if message.from_user is None:
        return

    await state.set_state(None)
    service = MarketplaceService(db_session)
    await service.ensure_user_from_telegram(
        telegram_user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    await message.answer(START_TEXT, reply_markup=role_keyboard())


@router.callback_query(F.data.in_({"role:citizen", "role:business"}))
async def select_role(
    callback: CallbackQuery,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    await state.set_state(None)
    service = MarketplaceService(db_session)
    user = await service.ensure_user_from_telegram(
        telegram_user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )

    role = UserRole.CITIZEN if callback.data.endswith("citizen") else UserRole.BUSINESS
    await service.set_user_role(user=user, role=role)
    await callback.answer("Rol guardado")

    if role is UserRole.CITIZEN:
        await callback.message.answer(
            CITIZEN_WELCOME_TEXT,
            reply_markup=citizen_menu_keyboard(),
        )
        return

    await callback.message.answer(
        BUSINESS_WELCOME_TEXT,
        reply_markup=business_menu_keyboard(),
    )
    await state.set_state(PublishOfferStates.waiting_business_name)
    await callback.message.answer(BUSINESS_NAME_PROMPT)
