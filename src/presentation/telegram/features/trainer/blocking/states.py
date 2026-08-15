from aiogram.fsm.state import State, StatesGroup


class TrainerBlockingSG(StatesGroup):
    select_date = State()
    confirm = State()