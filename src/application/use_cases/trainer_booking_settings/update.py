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
    # None — не менять
    no_show_charges_package: bool | None = None
    ask_attendance_confirmation: bool | None = None
    ask_rating: bool | None = None


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
            if command.no_show_charges_package is not None:
                existing.no_show_charges_package = command.no_show_charges_package
            if command.ask_attendance_confirmation is not None:
                existing.ask_attendance_confirmation = command.ask_attendance_confirmation
            if command.ask_rating is not None:
                existing.ask_rating = command.ask_rating
            saved = await self.settings_repo.save(existing)
        else:
            new_settings = TrainerBookingSettings(
                trainer_id=command.trainer_id,
                calendar_horizon_days=command.calendar_horizon_days,
                max_active_bookings_per_client=command.max_active_bookings_per_client,
                no_show_charges_package=(
                    command.no_show_charges_package
                    if command.no_show_charges_package is not None
                    else True
                ),
            )
            saved = await self.settings_repo.save(new_settings)

        await self.transaction_manager.commit()
        return saved