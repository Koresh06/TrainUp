from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)


@dataclass(frozen=True, eq=False)
class GetTrainerReminderSettingsRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetTrainerReminderSettingsUseCase(
    UseCase[GetTrainerReminderSettingsRequest, TrainerReminderSettings]
):
    settings_repo: TrainerReminderSettingsRepository

    async def __call__(
        self, command: GetTrainerReminderSettingsRequest
    ) -> TrainerReminderSettings:
        settings = await self.settings_repo.get_by_trainer_id(command.trainer_id)
        return settings or TrainerReminderSettings(trainer_id=command.trainer_id)
