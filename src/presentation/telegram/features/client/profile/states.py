from aiogram.fsm.state import State, StatesGroup


class ClientProfileSG(StatesGroup):
    main = State()
    questions = State()
    confirm = State()
