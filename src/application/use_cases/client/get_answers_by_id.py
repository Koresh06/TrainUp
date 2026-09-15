from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client_answer import ClientAnswer
from src.domain.repositories.client_answer import ClientAnswerRepository


@dataclass(frozen=True, eq=False)
class GetClientAnswersRequest(UseCaseRequest):
    client_id: int


@dataclass(kw_only=True)
class GetClientAnswersUseCase(UseCase[GetClientAnswersRequest, list[ClientAnswer]]):
    answer_repo: ClientAnswerRepository

    async def __call__(self, command: GetClientAnswersRequest) -> list[ClientAnswer]:
        return await self.answer_repo.get_by_client_id(command.client_id)
