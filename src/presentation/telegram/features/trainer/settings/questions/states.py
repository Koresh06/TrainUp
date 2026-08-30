from aiogram.fsm.state import State, StatesGroup


class TrainerQuestionsSG(StatesGroup):
    main = State()
    question_detail = State()
    add_option = State()
    add_question = State()