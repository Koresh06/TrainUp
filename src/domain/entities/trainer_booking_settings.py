from dataclasses import dataclass

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class TrainerBookingSettings(Entity):
    trainer_id: int
    calendar_horizon_days: int
    max_active_bookings_per_client: int