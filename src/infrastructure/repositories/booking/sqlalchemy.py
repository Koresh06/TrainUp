from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import BookingNotFoundException, SlotAlreadyBookedException
from src.domain.repositories.booking import BookingRepository
from src.infrastructure.database.models import BookingModel, CalendarSlotModel
from src.utils.get_datetime_utc_now import get_datetime_utc_now


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
        today = get_datetime_utc_now().date()
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.client_id == client_id,
                BookingModel.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                CalendarSlotModel.slot_date >= today,
            )
            .order_by(CalendarSlotModel.slot_date, CalendarSlotModel.start_time)
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_upcoming_by_trainer(self, trainer_id: int) -> list[Booking]:
        today = get_datetime_utc_now().date()
        query = (
            select(BookingModel)
            .join(CalendarSlotModel, BookingModel.slot_id == CalendarSlotModel.id)
            .where(
                BookingModel.trainer_id == trainer_id,
                BookingModel.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                CalendarSlotModel.slot_date >= today,
            )
            .order_by(CalendarSlotModel.slot_date, CalendarSlotModel.start_time)
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

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
