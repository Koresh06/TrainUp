from dataclasses import dataclass
from datetime import time
from decimal import Decimal

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_pricing_rule import TrainerPricingRule
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class UpdateTrainerPricingRuleRequest(UseCaseRequest):
    trainer_id: int
    boundary_time: time
    price_before: Decimal
    price_after: Decimal
    trainer_fee: Decimal | None


@dataclass(kw_only=True)
class UpdateTrainerPricingRuleUseCase(UseCase[UpdateTrainerPricingRuleRequest, TrainerPricingRule]):
    pricing_repo: TrainerPricingRuleRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: UpdateTrainerPricingRuleRequest) -> TrainerPricingRule:
        existing = await self.pricing_repo.get_by_trainer_id(command.trainer_id)

        if existing is not None:
            existing.boundary_time = command.boundary_time
            existing.price_before = command.price_before
            existing.price_after = command.price_after
            existing.trainer_fee = command.trainer_fee
            saved = await self.pricing_repo.save(existing)
        else:
            new_rule = TrainerPricingRule(
                trainer_id=command.trainer_id,
                boundary_time=command.boundary_time,
                price_before=command.price_before,
                price_after=command.price_after,
                trainer_fee=command.trainer_fee
            )
            saved = await self.pricing_repo.save(new_rule)

        await self.transaction_manager.commit()
        return saved