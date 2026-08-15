from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.slot_template import SlotTemplate
from src.domain.exception.slot_template import SlotTemplateNotFoundException
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.infrastructure.database.models import SlotTemplateModel


class SQLAlchemySlotTemplateRepo(SlotTemplateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_by_trainer(self, trainer_id: int) -> list[SlotTemplate]:
        query = select(SlotTemplateModel).where(
            SlotTemplateModel.trainer_id == trainer_id,
            SlotTemplateModel.is_active.is_(True),
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, slot_template_id: int) -> SlotTemplate | None:
        query = select(SlotTemplateModel).where(SlotTemplateModel.id == slot_template_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_by_trainer_and_weekday(self, trainer_id: int, weekday: int) -> list   [SlotTemplate]:
        query = select(SlotTemplateModel).where(
            SlotTemplateModel.trainer_id == trainer_id,
            SlotTemplateModel.weekday == weekday,
        )
        result = await self._session.execute(query)
        return [m.to_entity() for m in result.scalars().all()]

    async def save(self, slot_template: SlotTemplate) -> SlotTemplate:
        if slot_template.id == 0:
            model = SlotTemplateModel.from_entity(slot_template)
            self._session.add(model)
        else:
            query = select(SlotTemplateModel).where(SlotTemplateModel.id == slot_template.id)
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise SlotTemplateNotFoundException(slot_template_id=slot_template.id)
            model.update_model(slot_template)

        await self._session.flush()
        return model.to_entity()

    async def delete(self, slot_template: SlotTemplate) -> None:
        query = select(SlotTemplateModel).where(SlotTemplateModel.id == slot_template.id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise SlotTemplateNotFoundException(slot_template_id=slot_template.id)
        await self._session.delete(model)
        await self._session.flush()

    async def get_distinct_start_times(self, trainer_id: int) -> list[time]:
        query = (
            select(SlotTemplateModel.start_time)
            .where(
                SlotTemplateModel.trainer_id == trainer_id,
                SlotTemplateModel.is_active.is_(True),
            )
            .distinct()
            .order_by(SlotTemplateModel.start_time)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())