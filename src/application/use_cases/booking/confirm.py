from dataclasses import dataclass
from datetime import timedelta

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import (
    REMINDER_HOURS_BEFORE_TRAINING,
    REMINDER_TEST_DELAY_MINUTES,
    REMINDER_TEST_MODE,
)
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now
from src.domain.utils import get_training_datetime_utc


@dataclass(frozen=True, eq=False)
class ConfirmBookingRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class ConfirmBookingUseCase(UseCase[ConfirmBookingRequest, Booking]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    notification_service: NotificationService
    booking_scheduler: BookingScheduler
    transaction_manager: TransactionManager

    async def __call__(self, command: ConfirmBookingRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None:
            raise BookingNotFoundException(command.booking_id)

        booking.confirm()
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        client = await self.client_repo.get_by_id(booking.client_id)
        trainer = await self.trainer_repo.get_by_id(booking.trainer_id)
        slot = await self.slot_repo.get_by_id(booking.slot_id)

        if client is not None and trainer is not None and slot is not None:
            contact_lines = [
                f'💬 <a href="tg://user?id={trainer.tg_id}">Написать тренеру в Telegram</a>'
            ]
            if trainer.phone:
                contact_lines.append(f"📞 {trainer.phone}")
            contact_block = "\n".join(contact_lines)

            text = (
                f"✅ <b>Тренер подтвердил вашу запись!</b>\n\n"
                f"📅 {slot.slot_date.strftime('%d.%m.%Y')}\n"
                f"🕐 {slot.start_time.strftime('%H:%M')}\n\n"
                f"Если понадобится перенести время — свяжитесь с тренером напрямую:\n"
                f"{contact_block}"
            )
            await self.notification_service.send(chat_id=client.tg_id, text=text)

        if slot is not None:
            if REMINDER_TEST_MODE:
                remind_at_utc = get_datetime_utc_now() + timedelta(
                    minutes=REMINDER_TEST_DELAY_MINUTES
                )
            else:
                training_at_utc = get_training_datetime_utc(slot)
                remind_at_utc = training_at_utc - timedelta(
                    hours=REMINDER_HOURS_BEFORE_TRAINING
                )

            if remind_at_utc > get_datetime_utc_now():
                await self.booking_scheduler.schedule_training_reminder(
                    booking_id=saved.id,
                    remind_at_utc=remind_at_utc,
                )

        return saved
