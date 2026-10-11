from aiogram.fsm.state import State, StatesGroup


class TrainerHelpSG(StatesGroup):
    list = State()
    answer = State()
