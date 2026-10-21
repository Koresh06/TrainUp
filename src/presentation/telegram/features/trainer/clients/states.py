from aiogram.fsm.state import State, StatesGroup


class TrainerClientsSG(StatesGroup):
    list = State()
    detail = State()
    # новый клиент без Telegram
    add_name = State()
    add_phone = State()
    add_note = State()
    # редактирование карточки
    edit_menu = State()
    edit_value = State()
    invite = State()
    delete_confirm = State()
    # запись клиента тренером
    book_day = State()
    book_time = State()
    book_confirm = State()
    # абонементы и оплаты
    packages = State()
    package_detail = State()
    package_sessions = State()
    package_price = State()
    package_valid = State()
    package_paid = State()
    unpaid = State()
    debtors = State()
