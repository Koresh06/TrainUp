from aiogram.fsm.state import State, StatesGroup


class TrainerProfileSG(StatesGroup):
    main = State()
    preview = State()
    name = State()
    bio = State()
    phone = State()
    photo = State()
    social_links = State()
    group = State()
