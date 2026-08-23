from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import DEFAULT_PRICE_AFTER, DEFAULT_PRICE_BEFORE, DEFAULT_PRICING_BOUNDARY_TIME
from src.domain.entities.trainer_pricing_rule import TrainerPricingRule
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository


@dataclass(frozen=True, eq=False)
class GetTrainerPricingRuleRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetTrainerPricingRuleUseCase(UseCase[GetTrainerPricingRuleRequest, TrainerPricingRule]):
    pricing_repo: TrainerPricingRuleRepository

    async def __call__(self, command: GetTrainerPricingRuleRequest) -> TrainerPricingRule:
        rule = await self.pricing_repo.get_by_trainer_id(command.trainer_id)
        if rule is not None:
            return rule

        return TrainerPricingRule(
            trainer_id=command.trainer_id,
            boundary_time=DEFAULT_PRICING_BOUNDARY_TIME,
            price_before=DEFAULT_PRICE_BEFORE,
            price_after=DEFAULT_PRICE_AFTER,
        )