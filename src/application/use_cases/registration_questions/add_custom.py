from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.question_type import QuestionType
from src.domain.repositories.registration_question import RegistrationQuestionRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager



@dataclass(frozen=True, eq=False)
class AddCustomQuestionRequest(UseCaseRequest):
    trainer_id: int
    label: str


@dataclass(kw_only=True)
class AddCustomQuestionUseCase(UseCase[AddCustomQuestionRequest, RegistrationQuestion]):
    question_repo: RegistrationQuestionRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: AddCustomQuestionRequest) -> RegistrationQuestion:
        existing = await self.question_repo.get_all_by_trainer_id(command.trainer_id)
        next_order = (max((q.order for q in existing), default=-1)) + 1

        question = RegistrationQuestion(
            trainer_id=command.trainer_id,
            question_type=QuestionType.TEXT,
            label=command.label,
            options=[],
            order=next_order,
            is_system=False,
            system_key=None,
        )
        saved = await self.question_repo.save(question)
        await self.transaction_manager.commit()
        return saved