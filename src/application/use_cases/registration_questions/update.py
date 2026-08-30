from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.question_type import QuestionType
from src.domain.exception.registration_question import (
    RegistrationQuestionNotFoundException,
)
from src.domain.repositories.registration_question import RegistrationQuestionRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class UpdateQuestionOptionsRequest(UseCaseRequest):
    question_id: int
    options: list[str]


@dataclass(kw_only=True)
class UpdateQuestionOptionsUseCase(
    UseCase[UpdateQuestionOptionsRequest, RegistrationQuestion]
):
    question_repo: RegistrationQuestionRepository
    transaction_manager: TransactionManager

    async def __call__(
        self, command: UpdateQuestionOptionsRequest
    ) -> RegistrationQuestion:
        question = await self.question_repo.get_by_id(command.question_id)
        if question is None:
            raise RegistrationQuestionNotFoundException(command.question_id)
        if question.question_type != QuestionType.MULTI_SELECT:
            raise ValueError("Only MULTI_SELECT questions have options")

        question.options = command.options
        saved = await self.question_repo.save(question)
        await self.transaction_manager.commit()
        return saved
