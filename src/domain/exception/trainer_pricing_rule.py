from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class TrainerPricingRuleNotFoundException(DomainError):
    trainer_id: int

    @property
    def message(self) -> str:
        return f"Настройки цен для тренера с id {self.trainer_id} не найдены"