from aiogram.fsm.state import State, StatesGroup


class TrainerVacationSG(StatesGroup):
    list = State()
    pick_from = State()
    pick_to = State()
    preview = State()
    done = State()
    detail = State()
