from aiogram.fsm.state import State, StatesGroup


class BookingSG(StatesGroup):
    select_day = State()
    select_time = State()
    confirm = State()