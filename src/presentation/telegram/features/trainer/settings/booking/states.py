from aiogram.fsm.state import State, StatesGroup


class TrainerBookingSettingsSG(StatesGroup):
    main = State()
    edit_horizon = State()
    edit_max_bookings = State()
