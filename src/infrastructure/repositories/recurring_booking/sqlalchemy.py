from datetime import date, time

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.exception.recurring_booking import RecurringBookingNotFoundException
from src.infrastructure.database.models.recurring_booking import RecurringBookingModel


class SQLAlchemyRecurringBookingRepo(RecurringBookingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, recurring_booking_id: int) -> RecurringBooking | None:
        model = await self._session.get(RecurringBookingModel, recurring_booking_id)
        return model.to_entity() if model else None

    async def get_active_by_trainer_id(self, trainer_id: int) -> list[RecurringBooking]:
        stmt = select(RecurringBookingModel).where(
            RecurringBookingModel.trainer_id == trainer_id,
            RecurringBookingModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_all_active(self) -> list[RecurringBooking]:
        stmt = select(RecurringBookingModel).where(
            RecurringBookingModel.is_active.is_(True)
        )
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def save(self, recurring: RecurringBooking) -> RecurringBooking:
        if recurring.id == 0:
            model = RecurringBookingModel.from_entity(recurring)
            self._session.add(model)
        else:
            model = await self._session.get(RecurringBookingModel, recurring.id)
            if model is None:
                raise RecurringBookingNotFoundException(recurring.id)
            model.update_model(recurring)

        await self._session.flush()
        return model.to_entity()

    async def exists_active(
        self,
        trainer_id: int,
        client_id: int,
        weekday: int,
        start_time: time,
    ) -> bool:
        stmt = select(
            exists().where(
                RecurringBookingModel.trainer_id == trainer_id,
                RecurringBookingModel.client_id == client_id,
                RecurringBookingModel.weekday == weekday,
                RecurringBookingModel.start_time == start_time,
                RecurringBookingModel.is_active.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar()

    async def get_active_by_trainer_and_client(
        self, trainer_id: int, client_id: int
    ) -> list[RecurringBooking]:
        stmt = select(RecurringBookingModel).where(
            RecurringBookingModel.trainer_id == trainer_id,
            RecurringBookingModel.client_id == client_id,
            RecurringBookingModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]