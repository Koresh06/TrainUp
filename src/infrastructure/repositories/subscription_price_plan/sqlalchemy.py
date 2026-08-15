from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.exception.subscription import SubscriptionPricePlanNotFoundException
from src.domain.repositories.subscription_price_plan import SubscriptionPricePlanRepository
from src.infrastructure.database.models.subscription_price_plan import SubscriptionPricePlanModel

class SQLAlchemySubscriptionPricePlanRepo(SubscriptionPricePlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_plans(self) -> list[SubscriptionPricePlan]:
        query = (
            select(SubscriptionPricePlanModel)
            .where(SubscriptionPricePlanModel.is_active.is_(True))
            .order_by(SubscriptionPricePlanModel.months)
        )
        result = await self._session.execute(query)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_by_id(self, price_plan_id: int) -> SubscriptionPricePlan | None:
        query = select(SubscriptionPricePlanModel).where(
            SubscriptionPricePlanModel.id == price_plan_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, price_plan: SubscriptionPricePlan) -> SubscriptionPricePlan:
        if price_plan.id == 0:
            model = SubscriptionPricePlanModel.from_entity(price_plan)
            self._session.add(model)
        else:
            query = select(SubscriptionPricePlanModel).where(
                SubscriptionPricePlanModel.id == price_plan.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise SubscriptionPricePlanNotFoundException(price_plan_id=price_plan.id)
            model.update_model(price_plan)

        await self._session.flush()
        return model.to_entity()