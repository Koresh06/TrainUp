from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.feedback import FeedbackMessage
from src.domain.enums.request import RequestStatus
from src.domain.exception.feedback import FeedbackNotFoundException
from src.domain.repositories.feedback import FeedbackRepository
from src.infrastructure.database.models import FeedbackMessageModel


class SQLAlchemyFeedbackRepo(FeedbackRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[FeedbackMessage]:
        query = select(FeedbackMessageModel)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, feedback_id: int) -> FeedbackMessage | None:
        query = select(FeedbackMessageModel).where(FeedbackMessageModel.id == feedback_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, feedback: FeedbackMessage) -> FeedbackMessage:
        if feedback.id == 0:
            model = FeedbackMessageModel.from_entity(feedback)
            self._session.add(model)
        else:
            query = select(FeedbackMessageModel).where(
                FeedbackMessageModel.id == feedback.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise FeedbackNotFoundException(feedback_id=feedback.id)
            model.update_model(feedback)

        await self._session.flush()
        return model.to_entity()

    async def get_by_trainer_id(
        self, trainer_id: int, statuses: list[RequestStatus]
    ) -> list[FeedbackMessage]:
        query = (
            select(FeedbackMessageModel)
            .where(
                FeedbackMessageModel.trainer_id == trainer_id,
                FeedbackMessageModel.status.in_(statuses),
            )
            .order_by(FeedbackMessageModel.created_at.desc())
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def count_by_trainer_created_between(
        self, created_from: datetime, created_to: datetime
    ) -> dict[int, int]:
        query = (
            select(FeedbackMessageModel.trainer_id, func.count())
            .where(
                FeedbackMessageModel.created_at >= created_from,
                FeedbackMessageModel.created_at < created_to,
            )
            .group_by(FeedbackMessageModel.trainer_id)
        )
        result = await self._session.execute(query)
        return dict(result.all())
