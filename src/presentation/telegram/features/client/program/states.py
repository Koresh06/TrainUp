from aiogram.fsm.state import State, StatesGroup


class ClientProgramSG(StatesGroup):
    program_type = State()
    direction = State()
    comment = State()
    confirm = State()
