from aiogram.fsm.state import State, StatesGroup


class SubscriptionSG(StatesGroup):
    select_plan = State()
    confirm = State()


class TrainerOnboardingSG(StatesGroup):
    welcome = State()
    name = State()
    bio = State()
    group = State()
    final = State()