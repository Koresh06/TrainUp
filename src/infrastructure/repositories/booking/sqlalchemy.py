from datetime import date, datetime, time, timedelta

from sqlalchemy import desc, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.constants import PROJECT_TIMEZONE
from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import (
    BookingNotFoundException,
    SlotAlreadyBookedException,
)
from src.domain.repositories.booking import BookingRepository
from src.domain.utils import get_project_today
from src.infrastructure.database.models import BookingModel, CalendarSlotModel


class SQLAlchemyBookingRepo(BookingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Booking]:
        query = select(BookingModel)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, booking_id: int) -> Booking | None:
        query = select(BookingModel).where(BookingModel.id == booking_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_upcoming_by_client(self, client_id: int) -> list[Booking]:
        today = get_project_today()
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.client_id == client_id,
                BookingModel.status.in_(
                    [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
                CalendarSlotModel.slot_date >= today,
            )
            .order_by(CalendarSlotModel.slot_date, CalendarSlotModel.start_time)
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_upcoming_by_trainer(self, trainer_id: int) -> list[Booking]:
        today = get_project_today()
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.trainer_id == trainer_id,
                BookingModel.status.in_(
                    [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
                CalendarSlotModel.slot_date >= today,
            )
            .order_by(CalendarSlotModel.slot_date, CalendarSlotModel.start_time)
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def count_active_by_slot_id(self, slot_id: int) -> int:
        query = select(func.count(BookingModel.id)).where(
            BookingModel.slot_id == slot_id,
            BookingModel.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_active_by_slot_ids(self, slot_ids: list[int]) -> dict[int, int]:
        if not slot_ids:
            return {}
        query = (
            select(BookingModel.slot_id, func.count(BookingModel.id))
            .where(
                BookingModel.slot_id.in_(slot_ids),
                BookingModel.status.in_(
                    [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
            )
            .group_by(BookingModel.slot_id)
        )
        result = await self._session.execute(query)
        return dict(result.all())

    async def exists_active_by_client_and_slot(
        self, client_id: int, slot_id: int
    ) -> bool:
        query = select(
            exists().where(
                BookingModel.client_id == client_id,
                BookingModel.slot_id == slot_id,
                BookingModel.status.in_(
                    [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
            )
        )
        result = await self._session.execute(query)
        return result.scalar()

    async def save(self, booking: Booking) -> Booking:
        if booking.id == 0:
            model = BookingModel.from_entity(booking)
            self._session.add(model)
        else:
            query = select(BookingModel).where(BookingModel.id == booking.id)
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise BookingNotFoundException(booking_id=booking.id)
            model.update_model(booking)

        try:
            await self._session.flush()
        except IntegrityError as error:
            await self._session.rollback()
            raise SlotAlreadyBookedException(slot_id=booking.slot_id) from error

        return model.to_entity()

    async def delete(self, booking_id: int) -> None:
        query = select(BookingModel).where(BookingModel.id == booking_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise BookingNotFoundException(booking_id=booking_id)
        await self._session.delete(model)
        await self._session.flush()

    async def get_latest_by_recurring_booking_id(
        self, recurring_booking_id: int
    ) -> Booking | None:
        stmt = (
            select(BookingModel)
            .where(BookingModel.recurring_booking_id == recurring_booking_id)
            .order_by(desc(BookingModel.id))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_upcoming_by_recurring_booking_id(
        self, recurring_booking_id: int
    ) -> list[Booking]:
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.recurring_booking_id == recurring_booking_id,
                BookingModel.status.in_(
                    [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
                CalendarSlotModel.slot_date >= get_project_today(),
            )
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_past_confirmed(self, before_date: date) -> list[Booking]:
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.status == BookingStatus.CONFIRMED,
                CalendarSlotModel.slot_date < before_date,
            )
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_latest_completed_by_client(self, client_id: int) -> Booking | None:
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.client_id == client_id,
                BookingModel.status == BookingStatus.COMPLETED,
            )
            .order_by(
                CalendarSlotModel.slot_date.desc(), CalendarSlotModel.start_time.desc()
            )
            .limit(1)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def count_completed_by_trainer_in_period(
        self, trainer_id: int, date_from: date, date_to: date
    ) -> int:
        query = (
            select(func.count())
            .select_from(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.trainer_id == trainer_id,
                BookingModel.status == BookingStatus.COMPLETED,
                CalendarSlotModel.slot_date >= date_from,
                CalendarSlotModel.slot_date <= date_to,
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_cancelled_by_trainer_in_period(
        self, trainer_id: int, date_from: date, date_to: date
    ) -> int:
        query = (
            select(func.count())
            .select_from(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.trainer_id == trainer_id,
                BookingModel.status == BookingStatus.CANCELLED,
                # updated_at — timestamptz: сравнение с голой датой date_to
                # отрезало бы весь сегодняшний день, поэтому берём [начало date_from;
                # начало дня после date_to) в часовом поясе проекта
                BookingModel.updated_at >= datetime.combine(
                    date_from, time.min, tzinfo=PROJECT_TIMEZONE
                ),
                BookingModel.updated_at < datetime.combine(
                    date_to + timedelta(days=1), time.min, tzinfo=PROJECT_TIMEZONE
                ),
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_by_trainer_and_status(
        self, date_from: date, date_to: date
    ) -> dict[tuple[int, BookingStatus], int]:
        query = (
            select(BookingModel.trainer_id, BookingModel.status, func.count())
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                CalendarSlotModel.slot_date >= date_from,
                CalendarSlotModel.slot_date <= date_to,
            )
            .group_by(BookingModel.trainer_id, BookingModel.status)
        )
        result = await self._session.execute(query)
        return {(trainer_id, status): count for trainer_id, status, count in result.all()}

    async def get_history_by_trainer(
        self, trainer_id: int, limit: int = 50
    ) -> list[Booking]:
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.trainer_id == trainer_id,
                BookingModel.status.in_(
                    [BookingStatus.COMPLETED, BookingStatus.CANCELLED]
                ),
            )
            .order_by(
                CalendarSlotModel.slot_date.desc(), CalendarSlotModel.start_time.desc()
            )
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]
