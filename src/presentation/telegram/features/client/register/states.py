from aiogram.fsm.state import State, StatesGroup


class ClientRegisterSG(StatesGroup):
    welcome = State()
    full_name = State()
    age = State()
    phone = State()
    sport_experience = State()
    questions = State()
    confirm = State()