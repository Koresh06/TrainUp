from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import DEFAULT_CALENDAR_HORIZON_DAYS, DEFAULT_MAX_ACTIVE_BOOKINGS
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.exception.trainer_booking_settings import TrainerBookingSettingsNotFoundException
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository


@dataclass(frozen=True, eq=False)
class GetTrainerBookingSettingsRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetTrainerBookingSettingsUseCase(
    UseCase[GetTrainerBookingSettingsRequest, TrainerBookingSettings]
):
    settings_repo: TrainerBookingSettingsRepository

    async def __call__(self, command: GetTrainerBookingSettingsRequest) -> TrainerBookingSettings:
        settings = await self.settings_repo.get_by_trainer_id(command.trainer_id)
        if settings is not None:
            return settings

        raise TrainerBookingSettingsNotFoundException(trainer_id=command.trainer_id)