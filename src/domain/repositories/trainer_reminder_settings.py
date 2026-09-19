from typing import Protocol

from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings


class TrainerReminderSettingsRepository(Protocol):
    async def get_by_trainer_id(
        self, trainer_id: int
    ) -> TrainerReminderSettings | None: ...
    
    async def save(
        self, settings: TrainerReminderSettings
    ) -> TrainerReminderSettings: ...
