from aiogram.fsm.state import State, StatesGroup


class ClientFeedbackSG(StatesGroup):
    main = State()
    callback_confirm = State()
    callback_phone = State()
    message = State()
    faq_list = State()
    faq_answer = State()
