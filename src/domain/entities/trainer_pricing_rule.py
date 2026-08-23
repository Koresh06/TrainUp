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

    def price_for(self, slot_start_time: time) -> Decimal:
        if slot_start_time < self.boundary_time:
            return self.price_before
        return self.price_after