from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class InvalidVacationPeriodException(DomainError):
    @property
    def message(self) -> str:
        return "Период отпуска указан неверно"


@dataclass
class VacationNotFoundException(DomainError):
    vacation_id: int

    @property
    def message(self) -> str:
        return f"Отпуск {self.vacation_id} не найден"
