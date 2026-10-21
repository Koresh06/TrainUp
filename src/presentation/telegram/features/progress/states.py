from aiogram.fsm.state import State, StatesGroup


class ProgressSG(StatesGroup):
    """Дневник прогресса клиента — общий для тренера и самого клиента."""

    main = State()
    chart = State()
    add = State()
    add_photo = State()
    photos = State()
    photo = State()
    delete_confirm = State()
