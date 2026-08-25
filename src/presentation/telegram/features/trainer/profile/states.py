from aiogram.fsm.state import State, StatesGroup


class TrainerProfileSG(StatesGroup):
    main = State()
    edit_menu = State()
    photo = State()
    social_links = State()