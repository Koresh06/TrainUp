from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.repositories.registration_question import RegistrationQuestionRepository


@dataclass(frozen=True, eq=False)
class GetAllRegistrationQuestionsRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetAllRegistrationQuestionsUseCase(
    UseCase[GetAllRegistrationQuestionsRequest, list[RegistrationQuestion]]
):
    question_repo: RegistrationQuestionRepository

    async def __call__(
        self, command: GetAllRegistrationQuestionsRequest
    ) -> list[RegistrationQuestion]:
        return await self.question_repo.get_all_by_trainer_id(command.trainer_id)