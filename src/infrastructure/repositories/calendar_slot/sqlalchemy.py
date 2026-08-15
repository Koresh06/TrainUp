from datetime import date, time

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.enums.slot import SlotStatus
from src.domain.exception.calendar_slot import (
    CalendarSlotAlreadyExistsException,
    CalendarSlotNotFoundException,
)
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.infrastructure.database.models import CalendarSlotModel


class SQLAlchemyCalendarSlotRepo(CalendarSlotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, slot_id: int) -> CalendarSlot | None:
        query = select(CalendarSlotModel).where(CalendarSlotModel.id == slot_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_free_slots(
        self,
        trainer_id: int,
        date_from: date,
        date_to: date,
    ) -> list[CalendarSlot]:
        query = (
            select(CalendarSlotModel)
            .where(
                CalendarSlotModel.trainer_id == trainer_id,
                CalendarSlotModel.slot_date >= date_from,
                CalendarSlotModel.slot_date <= date_to,
                CalendarSlotModel.status == SlotStatus.FREE,
                CalendarSlotModel.is_active.is_(True),
            )
            .order_by(CalendarSlotModel.slot_date, CalendarSlotModel.start_time)
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def exists_for_datetime(
        self,
        trainer_id: int,
        slot_date: date,
        start_time: time,
    ) -> bool:
        query = (
            exists()
            .where(
                CalendarSlotModel.trainer_id == trainer_id,
                CalendarSlotModel.slot_date == slot_date,
                CalendarSlotModel.start_time == start_time,
            )
            .select()
        )
        result = await self._session.execute(query)
        return result.scalar()

    async def save(self, slot: CalendarSlot) -> CalendarSlot:
        if slot.id == 0:
            model = CalendarSlotModel.from_entity(slot)
            self._session.add(model)
        else:
            query = select(CalendarSlotModel).where(CalendarSlotModel.id == slot.id)
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise CalendarSlotNotFoundException(slot_id=slot.id)
            model.update_model(slot)

        try:
            await self._session.flush()
        except IntegrityError as error:
            await self._session.rollback()
            raise CalendarSlotAlreadyExistsException(
                trainer_id=slot.trainer_id,
                slot_date=slot.slot_date,
                start_time=slot.start_time,
            ) from error

        return model.to_entity()

    async def save_many(self, slots: list[CalendarSlot]) -> list[CalendarSlot]:
        models = [CalendarSlotModel.from_entity(slot) for slot in slots]
        self._session.add_all(models)

        try:
            await self._session.flush()
        except IntegrityError as error:
            await self._session.rollback()
            conflicting = slots[0]
            raise CalendarSlotAlreadyExistsException(
                trainer_id=conflicting.trainer_id,
                slot_date=conflicting.slot_date,
                start_time=conflicting.start_time,
            ) from error

        return [model.to_entity() for model in models]

    async def get_slots_for_date(
        self, trainer_id: int, slot_date: date
    ) -> list[CalendarSlot]:
        query = select(CalendarSlotModel).where(
            CalendarSlotModel.trainer_id == trainer_id,
            CalendarSlotModel.slot_date == slot_date,
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_slots_for_range(
        self,
        trainer_id: int,
        date_from: date,
        date_to: date,
    ) -> list[CalendarSlot]:
        query = select(CalendarSlotModel).where(
            CalendarSlotModel.trainer_id == trainer_id,
            CalendarSlotModel.slot_date >= date_from,
            CalendarSlotModel.slot_date <= date_to,
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]
