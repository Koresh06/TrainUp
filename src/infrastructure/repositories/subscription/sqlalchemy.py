from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionStatus
from src.domain.exception.subscription import TrainerSubscriptionNotFoundException
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.infrastructure.database.models import TrainerSubscriptionModel


class SQLAlchemyTrainerSubscriptionRepo(TrainerSubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_by_trainer_id(self, trainer_id: int) -> list[TrainerSubscription]:
        query = select(TrainerSubscriptionModel).where(
            TrainerSubscriptionModel.trainer_id == trainer_id,
            TrainerSubscriptionModel.status == SubscriptionStatus.ACTIVE,
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def save(self, subscription: TrainerSubscription) -> TrainerSubscription:
        if subscription.id == 0:
            model = TrainerSubscriptionModel.from_entity(subscription)
            self._session.add(model)
        else:
            query = select(TrainerSubscriptionModel).where(
                TrainerSubscriptionModel.id == subscription.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise TrainerSubscriptionNotFoundException(subscription_id=subscription.id)
            model.update_model(subscription)

        await self._session.flush()
        return model.to_entity()
