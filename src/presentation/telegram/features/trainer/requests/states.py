from aiogram.fsm.state import State, StatesGroup


class TrainerRequestsSG(StatesGroup):
    list = State()
    detail = State()
