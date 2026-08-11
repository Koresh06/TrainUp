from dataclasses import dataclass
from datetime import time

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.slot_template import SlotTemplateRepository


@dataclass(frozen=True, eq=False)
class GetTimeColumnsRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetTimeColumnsUseCase(UseCase[GetTimeColumnsRequest, list[time]]):
    template_repo: SlotTemplateRepository

    async def __call__(self, command: GetTimeColumnsRequest) -> list[time]:
        return await self.template_repo.get_distinct_start_times(command.trainer_id)