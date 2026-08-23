from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class TrainerBookingSettingsNotFoundException(DomainError):
    trainer_id: int

    @property
    def message(self) -> str:
        return f"Настройки записи для тренера с id {self.trainer_id} не найдены"