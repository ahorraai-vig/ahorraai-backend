from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PublishOfferStates(StatesGroup):
    waiting_business_name = State()
    waiting_offer_title = State()
    waiting_offer_description = State()
    waiting_offer_price = State()
