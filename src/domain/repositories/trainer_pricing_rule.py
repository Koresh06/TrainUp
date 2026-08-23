from typing import Protocol

from src.domain.entities.trainer_pricing_rule import TrainerPricingRule


class TrainerPricingRuleRepository(Protocol):
    async def get_by_trainer_id(self, trainer_id: int) -> TrainerPricingRule | None:
        ...
    async def save(self, rule: TrainerPricingRule) -> TrainerPricingRule:
        ...