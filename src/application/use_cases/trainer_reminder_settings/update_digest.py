from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class UpdateTrainerDigestSettingsRequest(UseCaseRequest):
    trainer_id: int
    morning_digest_hour: int | None
    evening_digest_hour: int | None
    digest_on_empty_days: bool


@dataclass(kw_only=True)
class UpdateTrainerDigestSettingsUseCase(
    UseCase[UpdateTrainerDigestSettingsRequest, TrainerReminderSettings]
):
    settings_repo: TrainerReminderSettingsRepository
    transaction_manager: TransactionManager

    async def __call__(
        self, command: UpdateTrainerDigestSettingsRequest
    ) -> TrainerReminderSettings:
        settings = await self.settings_repo.get_by_trainer_id(command.trainer_id)
        settings = settings or TrainerReminderSettings(trainer_id=command.trainer_id)
        settings.morning_digest_hour = command.morning_digest_hour
        settings.evening_digest_hour = command.evening_digest_hour
        settings.digest_on_empty_days = command.digest_on_empty_days
        settings.touch()
        saved = await self.settings_repo.save(settings)
        await self.transaction_manager.commit()
        return saved
