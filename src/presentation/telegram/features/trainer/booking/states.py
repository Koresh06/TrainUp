from aiogram.fsm.state import State, StatesGroup


class TrainerBookingsSG(StatesGroup):
    """«📅 Расписание» тренера."""

    day = State()
    week = State()
    pick_date = State()
    pending = State()
    history = State()
    detail = State()
    cancel_confirm = State()
    reschedule_day = State()
    reschedule_time = State()
    reschedule_confirm = State()
    # записать клиента на выбранный день
    add_client = State()
    add_time = State()
    add_confirm = State()
