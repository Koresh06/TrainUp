from aiogram.fsm.state import State, StatesGroup


class ClientConsultationSG(StatesGroup):
    consultation_type = State()
    comment = State()
    confirm = State()
