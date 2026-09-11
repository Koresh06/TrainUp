from aiogram.fsm.state import State, StatesGroup


class TrainerRecurringSG(StatesGroup):
    select_client = State()
    select_day = State()
    select_time = State()
    confirm = State()
