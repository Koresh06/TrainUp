from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class RecurringBookingNotFoundException(DomainError):
    id: int

    @property
    def message(self) -> str:
        return f"Повторяющаяся запись с id {self.id} не найдена"