from datetime import time
from typing import Protocol

from src.domain.entities.slot_template import SlotTemplate


class SlotTemplateRepository(Protocol):
    async def get_active_by_trainer(self, trainer_id: int) -> list[SlotTemplate]: ...

    async def get_by_id(self, slot_template_id: int) -> SlotTemplate | None: ...

    async def get_by_trainer_and_weekday(
        self,
        trainer_id: int,
        weekday: int,
    ) -> list[SlotTemplate]: ...

    async def save(self, slot_template: SlotTemplate) -> SlotTemplate: ...

    async def delete(self, slot_template: SlotTemplate) -> None: ...

    async def get_distinct_start_times(self, trainer_id: int) -> list[time]: ...
