from aiogram.fsm.state import State, StatesGroup


class TrainerReminderSettingsSG(StatesGroup):
    main = State()
    edit_hours = State()
