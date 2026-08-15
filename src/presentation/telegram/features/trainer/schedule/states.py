from aiogram.fsm.state import State, StatesGroup


class TrainerScheduleSG(StatesGroup):
    main = State()
    manage_weekday = State()