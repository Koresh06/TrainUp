from dataclasses import dataclass
from datetime import time
from decimal import Decimal

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class TrainerPricingRule(Entity):
    trainer_id: int
    boundary_time: time
    price_before: Decimal
    price_after: Decimal
    trainer_fee: Decimal | None = None  # опциональная доплата за работу тренера

    def price_for(self, slot_start_time: time) -> Decimal:
        return (
            self.price_before
            if slot_start_time < self.boundary_time
            else self.price_after
        )

    def format_price(self, slot_start_time: time) -> str:
        base = self.price_for(slot_start_time)
        if self.trainer_fee is None:
            return f"{base:.0f} BYN"
        total = base + self.trainer_fee
        return f"{base:.0f} BYN + {self.trainer_fee:.0f} BYN (работа тренера) = {total:.0f} BYN"
