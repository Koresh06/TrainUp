from datetime import timedelta
import logging
from dataclasses import dataclass

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.domain.constants import REMINDER_HOURS_BEFORE_TRAINING, REMINDER_TEST_DELAY_MINUTES, REMINDER_TEST_MODE
from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import BookingNotFoundException
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.interfaces.notification_service import NotificationService
from src.domain.utils import get_training_datetime_utc
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class RescheduleBookingRequest(UseCaseRequest):
    booking_id: int
    new_slot_id: int


@dataclass(kw_only=True)
class RescheduleBookingUseCase(UseCase[RescheduleBookingRequest, Booking]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    calendar_service: CalendarService
    pricing_rule_repo: TrainerPricingRuleRepository
    notification_service: NotificationService
    booking_scheduler: BookingScheduler
    transaction_manager: TransactionManager

    async def __call__(self, command: RescheduleBookingRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None:
            raise BookingNotFoundException(command.booking_id)

        old_slot_id = booking.slot_id
        new_slot = await self.slot_repo.get_by_id(command.new_slot_id)
        if new_slot is None:
            raise CalendarSlotNotFoundException(command.new_slot_id)

        # бронируем новый слот с обычной проверкой capacity (это не про
        # постоянных клиентов — разовый перенос уважает лимит мест)
        await self.calendar_service.book_slot(command.new_slot_id)

        # освобождаем старый слот
        await self.calendar_service.release_slot(old_slot_id)

        # пересчитываем цену под новое время
        pricing_rule = await self.pricing_rule_repo.get_by_trainer_id(booking.trainer_id)
        booking.price = (
            pricing_rule.price_for(new_slot.start_time) if pricing_rule is not None else None
        )
        booking.slot_id = command.new_slot_id
        booking.touch()
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        # переносим напоминание
        if booking.reminder_job_id:
            await self.booking_scheduler.cancel_training_reminder(booking_id=booking.id)

        if booking.status == BookingStatus.CONFIRMED:
            if REMINDER_TEST_MODE:
                remind_at_utc = get_datetime_utc_now() + timedelta(minutes=REMINDER_TEST_DELAY_MINUTES)
            else:
                training_at_utc = get_training_datetime_utc(new_slot)
                remind_at_utc = training_at_utc - timedelta(hours=REMINDER_HOURS_BEFORE_TRAINING)

            if remind_at_utc > get_datetime_utc_now():
                await self.booking_scheduler.schedule_training_reminder(
                    booking_id=saved.id, remind_at_utc=remind_at_utc,
                )

        client = await self.client_repo.get_by_id(booking.client_id)
        if client is not None:
            await self.notification_service.send(
                chat_id=client.tg_id,
                text=(
                    f"🔁 <b>Тренер перенёс вашу тренировку</b>\n\n"
                    f"📅 Новая дата: {new_slot.slot_date.strftime('%d.%m.%Y')}\n"
                    f"🕐 Новое время: {new_slot.start_time.strftime('%H:%M')}"
                ),
            )

        return saved