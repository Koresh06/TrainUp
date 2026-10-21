from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.booking import BookingActor


@dataclass(kw_only=True)
class ClientMeasurement(Entity):
    """Запись дневника прогресса: вес, обхваты и (по желанию) фото."""

    trainer_id: int
    client_id: int
    measured_on: date
    weight: Decimal | None = None  # кг
    waist: Decimal | None = None   # см
    chest: Decimal | None = None
    hips: Decimal | None = None
    photo_file_id: str | None = None
    added_by: BookingActor = BookingActor.TRAINER

    @property
    def is_empty(self) -> bool:
        return all(
            v is None for v in (self.weight, self.waist, self.chest, self.hips, self.photo_file_id)
        )
