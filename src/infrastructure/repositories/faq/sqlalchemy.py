from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.faq import FaqItem
from src.domain.exception.faq import FaqItemNotFoundException
from src.domain.repositories.faq import FaqRepository
from src.infrastructure.database.models import FaqItemModel


class SQLAlchemyFaqRepo(FaqRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[FaqItem]:
        query = select(FaqItemModel)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, faq_id: int) -> FaqItem | None:
        query = select(FaqItemModel).where(FaqItemModel.id == faq_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, faq_item: FaqItem) -> FaqItem:
        if faq_item.id == 0:
            model = FaqItemModel.from_entity(faq_item)
            self._session.add(model)
        else:
            query = select(FaqItemModel).where(FaqItemModel.id == faq_item.id)
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise FaqItemNotFoundException(faq_id=faq_item.id)
            model.update_model(faq_item)

        await self._session.flush()
        return model.to_entity()

    async def get_active(self) -> list[FaqItem]:
        query = (
            select(FaqItemModel)
            .where(FaqItemModel.is_active.is_(True))
            .order_by(FaqItemModel.order)
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]
