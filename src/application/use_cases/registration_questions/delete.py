from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.exception.registration_question import CannotDeleteSystemQuestionError, RegistrationQuestionNotFoundException
from src.domain.repositories.registration_question import RegistrationQuestionRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class DeleteCustomQuestionRequest(UseCaseRequest):
    question_id: int


@dataclass(kw_only=True)
class DeleteCustomQuestionUseCase(UseCase[DeleteCustomQuestionRequest, None]):
    question_repo: RegistrationQuestionRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: DeleteCustomQuestionRequest) -> None:
        question = await self.question_repo.get_by_id(command.question_id)
        if question is None:
            raise RegistrationQuestionNotFoundException(command.question_id)
        if question.is_system:
            raise CannotDeleteSystemQuestionError(command.question_id)

        await self.question_repo.delete(command.question_id)
        await self.transaction_manager.commit()
