from aiogram.fsm.state import State, StatesGroup


class ClientRegisterSG(StatesGroup):
    welcome = State()
    full_name = State()
    age = State()
    phone = State()
    sport_experience = State()
    health_conditions = State()
    goals = State()
    confirm = State()