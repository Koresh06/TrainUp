from typing import Protocol

from src.domain.entities.slot_template import SlotTemplate


class SlotTemplateRepository(Protocol):
    async def get_active_by_trainer(self, trainer_id: int) -> list[SlotTemplate]:
        ...

    async def save(self, slot_template: SlotTemplate) -> SlotTemplate:
        ...

    async def delete(self, slot_template: SlotTemplate) -> None:
        ...