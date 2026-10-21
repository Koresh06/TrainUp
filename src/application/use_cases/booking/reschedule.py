import logging
from dataclasses import dataclass

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import (
    BookingNotFoundException,
    BookingStatusTransitionException,
)
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.repositories.trainer_reminder_settings import TrainerReminderSettingsRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking._shared import _schedule_booking_jobs
from src.application.interfaces.notification_service import NotificationService
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class RescheduleBookingRequest(UseCaseRequest):
    booking_id: int
    new_slot_id: int
    # True — без проверки вместимости (тренировки постоянного клиента)
    force: bool = False


@dataclass(kw_only=True)
class RescheduleBookingUseCase(UseCase[RescheduleBookingRequest, Booking]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    slot_repo: CalendarSlotRepository
    calendar_service: CalendarService
    pricing_rule_repo: TrainerPricingRuleRepository
    reminder_settings_repo: TrainerReminderSettingsRepository
    notification_service: NotificationService
    booking_scheduler: BookingScheduler
    transaction_manager: TransactionManager

    async def __call__(self, command: RescheduleBookingRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None:
            raise BookingNotFoundException(command.booking_id)
        if not booking.is_active():
            raise BookingStatusTransitionException(
                booking_id=booking.id, status=booking.status
            )

        old_slot_id = booking.slot_id
        if old_slot_id == command.new_slot_id:
            return booking

        new_slot = await self.slot_repo.get_by_id(command.new_slot_id)
        if new_slot is None:
            raise CalendarSlotNotFoundException(command.new_slot_id)

        if command.force:
            await self.calendar_service.book_slot_forced(command.new_slot_id)
        else:
            await self.calendar_service.book_slot(command.new_slot_id)
        await self.calendar_service.release_slot(old_slot_id)

        pricing_rule = await self.pricing_rule_repo.get_by_trainer_id(booking.trainer_id)
        booking.price = (
            pricing_rule.price_for(new_slot.start_time) if pricing_rule is not None else None
        )
        booking.slot_id = command.new_slot_id
        booking.reset_attendance()
        booking.touch()
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        if booking.reminder_job_id:
            await self.booking_scheduler.cancel_training_reminder(booking_id=booking.id)
        if booking.completion_job_id:
            await self.booking_scheduler.cancel_booking_completion(booking_id=booking.id)
        await self.transaction_manager.commit()

        client = await self.client_repo.get_by_id(booking.client_id)
        has_telegram = client is not None and client.has_telegram

        if booking.status == BookingStatus.CONFIRMED:
            await _schedule_booking_jobs(
                booking_id=saved.id,
                trainer_id=booking.trainer_id,
                slot=new_slot,
                reminder_settings_repo=self.reminder_settings_repo,
                booking_scheduler=self.booking_scheduler,
                transaction_manager=self.transaction_manager,
                send_reminder=has_telegram,
            )

        if has_telegram:
            await self.notification_service.send(
                chat_id=client.tg_id,
                text=(
                    f"🔁 <b>Тренер перенёс вашу тренировку</b>\n\n"
                    f"📅 Новая дата: {new_slot.slot_date.strftime('%d.%m.%Y')}\n"
                    f"🕐 Новое время: {new_slot.start_time.strftime('%H:%M')}"
                ),
            )

        logger.info(
            "[RescheduleBooking:done] booking_id=%s %s -> %s",
            booking.id, old_slot_id, command.new_slot_id,
        )
        return saved
