from aiogram.fsm.state import State, StatesGroup


class ClientMenuSG(StatesGroup):
    main = State()
    trainer_profile = State()