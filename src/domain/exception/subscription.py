from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class TrainerSubscriptionNotFoundException(DomainError):
    subscription_id: int

    @property
    def message(self) -> str:
        return f"Подписка тренера с id {self.subscription_id} не найдена"


@dataclass
class SubscriptionPricePlanNotFoundException(DomainError):
    price_plan_id: int

    @property
    def message(self) -> str:
        return f"Тарифный план с id {self.price_plan_id} не найден"