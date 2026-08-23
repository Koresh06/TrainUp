from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class UpdateTrainerBookingSettingsRequest(UseCaseRequest):
    trainer_id: int
    calendar_horizon_days: int
    max_active_bookings_per_client: int


@dataclass(kw_only=True)
class UpdateTrainerBookingSettingsUseCase(
    UseCase[UpdateTrainerBookingSettingsRequest, TrainerBookingSettings]
):
    settings_repo: TrainerBookingSettingsRepository
    transaction_manager: TransactionManager

    async def __call__(
        self, command: UpdateTrainerBookingSettingsRequest
    ) -> TrainerBookingSettings:
        existing = await self.settings_repo.get_by_trainer_id(command.trainer_id)

        if existing is not None:
            existing.calendar_horizon_days = command.calendar_horizon_days
            existing.max_active_bookings_per_client = command.max_active_bookings_per_client
            saved = await self.settings_repo.save(existing)
        else:
            new_settings = TrainerBookingSettings(
                trainer_id=command.trainer_id,
                calendar_horizon_days=command.calendar_horizon_days,
                max_active_bookings_per_client=command.max_active_bookings_per_client,
            )
            saved = await self.settings_repo.save(new_settings)

        await self.transaction_manager.commit()
        return saved