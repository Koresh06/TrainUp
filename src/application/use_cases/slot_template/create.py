from dataclasses import dataclass
from datetime import time

from src.domain.entities.slot_template import SlotTemplate
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class CreateSlotTemplateRequest(UseCaseRequest):
    trainer_id: int
    weekday: int
    start_time: time
    end_time: time


@dataclass(kw_only=True)
class CreateSlotTemplateUseCase(UseCase[CreateSlotTemplateRequest, SlotTemplate]):
    template_repo: SlotTemplateRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateSlotTemplateRequest) -> SlotTemplate:
        template = SlotTemplate(
            trainer_id=command.trainer_id,
            weekday=command.weekday,
            start_time=command.start_time,
            end_time=command.end_time,
            is_active=True,
        )
        saved = await self.template_repo.save(template)
        await self.transaction_manager.commit()
        return saved

