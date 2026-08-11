from aiogram.fsm.state import State, StatesGroup


class ClientRegisterSG(StatesGroup):
    welcome = State()
    phone = State()
    age = State()
    goals = State()
    health_notes = State()
    injuries = State()
    confirm = State()