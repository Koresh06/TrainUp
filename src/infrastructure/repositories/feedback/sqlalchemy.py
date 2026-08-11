from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.feedback import FeedbackMessage
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

    async def get_unread(self) -> list[FeedbackMessage]:
        query = select(FeedbackMessageModel).where(FeedbackMessageModel.is_read.is_(False))
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

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
