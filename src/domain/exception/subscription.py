from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class TrainerSubscriptionNotFoundException(DomainError):
    subscription_id: int

    @property
    def message(self) -> str:
        return f"Подписка тренера с id {self.subscription_id} не найдена"
