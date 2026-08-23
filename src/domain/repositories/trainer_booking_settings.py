from typing import Protocol

from src.domain.entities.trainer_booking_settings import TrainerBookingSettings


class TrainerBookingSettingsRepository(Protocol):
    async def get_by_trainer_id(self, trainer_id: int) -> TrainerBookingSettings | None:
        ...
    async def save(self, settings: TrainerBookingSettings) -> TrainerBookingSettings:
        ...