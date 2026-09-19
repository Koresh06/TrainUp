from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class UpdateTrainerReminderSettingsRequest(UseCaseRequest):
    trainer_id: int
    hours_before: int


@dataclass(kw_only=True)
class UpdateTrainerReminderSettingsUseCase(
    UseCase[UpdateTrainerReminderSettingsRequest, TrainerReminderSettings]
):
    settings_repo: TrainerReminderSettingsRepository
    transaction_manager: TransactionManager

    async def __call__(
        self, command: UpdateTrainerReminderSettingsRequest
    ) -> TrainerReminderSettings:
        existing = await self.settings_repo.get_by_trainer_id(command.trainer_id)
        if existing is not None:
            existing.hours_before = command.hours_before
            saved = await self.settings_repo.save(existing)
        else:
            saved = await self.settings_repo.save(
                TrainerReminderSettings(
                    trainer_id=command.trainer_id,
                    hours_before=command.hours_before,
                )
            )
        await self.transaction_manager.commit()
        return saved
