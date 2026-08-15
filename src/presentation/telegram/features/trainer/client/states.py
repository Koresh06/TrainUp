from aiogram.fsm.state import State, StatesGroup


class TrainerClientsSG(StatesGroup):
    list = State()
