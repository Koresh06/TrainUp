from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.repositories.registration_question import RegistrationQuestionRepository


@dataclass(frozen=True, eq=False)
class GetActiveRegistrationQuestionsRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetActiveRegistrationQuestionsUseCase(
    UseCase[GetActiveRegistrationQuestionsRequest, list[RegistrationQuestion]]
):
    question_repo: RegistrationQuestionRepository

    async def __call__(
        self, command: GetActiveRegistrationQuestionsRequest
    ) -> list[RegistrationQuestion]:
        return await self.question_repo.get_active_by_trainer_id(command.trainer_id)
