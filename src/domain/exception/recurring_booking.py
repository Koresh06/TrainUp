from dataclasses import dataclass
from datetime import time

from src.domain.exception.base import DomainError


@dataclass
class RecurringBookingNotFoundException(DomainError):
    id: int

    @property
    def message(self) -> str:
        return f"Повторяющаяся запись с id {self.id} не найдена"


@dataclass
class RecurringBookingAlreadyExistsException(DomainError):
    trainer_id: int
    client_id: int
    weekday: int
    start_time: time

    @property
    def message(self) -> str:
        return f"Повторяющаяся запись тренера с id {self.trainer_id} на {self.weekday} {self.start_time} уже существует"
