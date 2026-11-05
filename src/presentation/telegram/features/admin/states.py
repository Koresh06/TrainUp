from aiogram.fsm.state import State, StatesGroup


class AdminMenuSG(StatesGroup):
    main = State()


class AdminStatsSG(StatesGroup):
    main = State()
    users = State()
    charts = State()


class AdminTrainersSG(StatesGroup):
    list = State()
    card = State()
    grant_type = State()
    grant_plan = State()
    grant_days = State()
    grant_confirm = State()
    block_confirm = State()


class AdminClientsSG(StatesGroup):
    search = State()
    list = State()
    card = State()


class AdminMailingSG(StatesGroup):
    target = State()
    select_trainer = State()
    compose = State()
    confirm = State()


class AdminFaqSG(StatesGroup):
    audience = State()
    list = State()
    detail = State()
    add_question = State()
    add_answer = State()


class AdminExportSG(StatesGroup):
    main = State()


class AdminApplicationsSG(StatesGroup):
    list = State()
    card = State()


class AdminStaffSG(StatesGroup):
    list = State()
    add = State()
    card = State()
    remove_confirm = State()


class AdminNotificationsSG(StatesGroup):
    main = State()


class AdminPricesSG(StatesGroup):
    list = State()
    edit = State()
