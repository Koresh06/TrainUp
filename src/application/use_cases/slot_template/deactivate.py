from dataclasses import dataclass

from src.domain.entities.slot_template import SlotTemplate
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.exception.slot_template import SlotTemplateNotFoundException
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.application.use_cases.base import UseCase, UseCaseRequest


@dataclass(frozen=True, eq=False)
class DeactivateSlotTemplateRequest(UseCaseRequest):
    slot_template_id: int


@dataclass(kw_only=True)
class DeactivateSlotTemplateUseCase(UseCase[DeactivateSlotTemplateRequest, SlotTemplate]):
    template_repo: SlotTemplateRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: DeactivateSlotTemplateRequest) -> SlotTemplate:
        template = await self.template_repo.get_by_id(command.slot_template_id)
        if template is None:
            raise SlotTemplateNotFoundException(command.slot_template_id)

        template.is_active = False
        saved = await self.template_repo.save(template)
        await self.transaction_manager.commit()
        return saved