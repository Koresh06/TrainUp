from aiogram.fsm.state import State, StatesGroup


class TrainerRecurringSG(StatesGroup):
    list = State()
    client_bookings = State() 
    select_client = State()
    select_day = State()
    select_time = State()
    confirm = State()
    detail = State()
    edit_day = State()
    edit_time = State()
    edit_confirm = State()