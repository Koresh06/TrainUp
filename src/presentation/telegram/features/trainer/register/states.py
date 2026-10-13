from aiogram.fsm.state import State, StatesGroup


class SubscriptionSG(StatesGroup):
    select_plan = State()
    select_method = State()
    payment = State()
    benefits = State()


class TrainerOnboardingSG(StatesGroup):
    welcome = State()
    name = State()
    phone = State()
    bio = State()
    photo = State()
    group = State()
    final = State()
    trial_started = State()
    benefits = State()