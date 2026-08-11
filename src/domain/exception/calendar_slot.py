from dataclasses import dataclass
from datetime import date, time

from src.domain.exception.base import DomainError


@dataclass
class CalendarSlotNotFoundException(DomainError):
    slot_id: int

    @property
    def message(self) -> str:
        return f"Слот с id {self.slot_id} не найден"


@dataclass
class CalendarSlotAlreadyExistsException(DomainError):
    trainer_id: int
    slot_date: date
    start_time: time

    @property
    def message(self) -> str:
        return (
            f"Слот тренера с id {self.trainer_id} на {self.slot_date} "
            f"{self.start_time} уже существует"
        )
