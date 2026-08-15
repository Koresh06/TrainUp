from dataclasses import dataclass

from src.domain.entities.slot_template import SlotTemplate
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.application.use_cases.base import UseCase, UseCaseRequest


@dataclass(frozen=True, eq=False)
class GetActiveSlotTemplatesRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetActiveSlotTemplatesUseCase(UseCase[GetActiveSlotTemplatesRequest, list[SlotTemplate]]):
    template_repo: SlotTemplateRepository

    async def __call__(self, command: GetActiveSlotTemplatesRequest) -> list[SlotTemplate]:
        return await self.template_repo.get_active_by_trainer(command.trainer_id)
