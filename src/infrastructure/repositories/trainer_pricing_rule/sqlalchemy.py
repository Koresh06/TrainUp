from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trainer_pricing_rule import TrainerPricingRule
from src.domain.exception.trainer_pricing_rule import TrainerPricingRuleNotFoundException
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.infrastructure.database.models.trainer_pricing_rule import TrainerPricingRuleModel


class SQLAlchemyTrainerPricingRuleRepo(TrainerPricingRuleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_trainer_id(self, trainer_id: int) -> TrainerPricingRule | None:
        query = select(TrainerPricingRuleModel).where(
            TrainerPricingRuleModel.trainer_id == trainer_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, rule: TrainerPricingRule) -> TrainerPricingRule:
        if rule.id == 0:
            model = TrainerPricingRuleModel.from_entity(rule)
            self._session.add(model)
        else:
            query = select(TrainerPricingRuleModel).where(
                TrainerPricingRuleModel.id == rule.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise TrainerPricingRuleNotFoundException(trainer_id=rule.trainer_id)
            model.update_model(rule)

        await self._session.flush()
        return model.to_entity()