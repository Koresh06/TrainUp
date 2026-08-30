from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.repositories.registration_question import RegistrationQuestionRepository


@dataclass(frozen=True, eq=False)
class GetRegistrationQuestionByIdRequest(UseCaseRequest):
    question_id: int


@dataclass(kw_only=True)
class GetRegistrationQuestionByIdUseCase(
    UseCase[GetRegistrationQuestionByIdRequest, RegistrationQuestion | None]
):
    question_repo: RegistrationQuestionRepository

    async def __call__(
        self, command: GetRegistrationQuestionByIdRequest
    ) -> RegistrationQuestion | None:
        return await self.question_repo.get_by_id(command.question_id)
