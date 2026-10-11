from aiogram.fsm.state import State, StatesGroup


class SubscriptionSG(StatesGroup):
    select_plan = State()
    select_method = State()
    payment = State()


class TrainerOnboardingSG(StatesGroup):
    welcome = State()
    name = State()
    phone = State()
    bio = State()
    photo = State()
    group = State()
    final = State()