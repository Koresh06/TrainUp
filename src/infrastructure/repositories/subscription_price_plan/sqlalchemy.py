from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.exception.subscription import SubscriptionPricePlanNotFoundException
from src.domain.repositories.subscription_price_plan import (
    SubscriptionPricePlanRepository,
)
from src.infrastructure.database.models.subscription_price_plan import (
    SubscriptionPricePlanModel,
)


class SQLAlchemySubscriptionPricePlanRepo(SubscriptionPricePlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_plans(self) -> list[SubscriptionPricePlan]:
        stmt = select(SubscriptionPricePlanModel).where(
            SubscriptionPricePlanModel.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_all(self) -> list[SubscriptionPricePlan]:
        stmt = select(SubscriptionPricePlanModel)
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_by_id(self, price_plan_id: int) -> SubscriptionPricePlan | None:
        model = await self._session.get(SubscriptionPricePlanModel, price_plan_id)
        return model.to_entity() if model else None

    async def save(self, price_plan: SubscriptionPricePlan) -> SubscriptionPricePlan:
        if price_plan.id == 0:
            model = SubscriptionPricePlanModel.from_entity(price_plan)
            self._session.add(model)
        else:
            model = await self._session.get(SubscriptionPricePlanModel, price_plan.id)
            if model is None:
                raise SubscriptionPricePlanNotFoundException(price_plan.id)
            model.update_model(price_plan)

        await self._session.flush()
        return model.to_entity()
