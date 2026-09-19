from aiogram.fsm.state import State, StatesGroup


class TrainerPricingRuleSG(StatesGroup):
    main = State()
    edit_boundary_time = State()
    edit_price_before = State()
    edit_price_after = State()
    edit_trainer_fee = State()