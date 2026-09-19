from aiogram.fsm.state import State, StatesGroup


class TrainerBookingsSG(StatesGroup):
    mode = State()   
    list = State()
    detail = State()
    reschedule_day = State()
    reschedule_time = State()
    reschedule_confirm = State()