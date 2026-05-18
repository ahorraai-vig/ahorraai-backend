from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PublishOfferStates(StatesGroup):
    waiting_business_name = State()
    waiting_offer_title = State()
    waiting_offer_description = State()
    waiting_offer_price = State()


class SearchCatalogStates(StatesGroup):
    waiting_query = State()


class DeliveryOrderStates(StatesGroup):
    waiting_contact_name = State()
    waiting_contact_phone = State()
    waiting_delivery_address = State()
    waiting_postal_code = State()
    waiting_delivery_city = State()
