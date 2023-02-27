from aiogram.dispatcher.filters.state import StatesGroup, State


class Register(StatesGroup):
    city = State()