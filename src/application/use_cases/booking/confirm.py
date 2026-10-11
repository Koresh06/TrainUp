from dataclasses import dataclass

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking._shared import _schedule_booking_jobs
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class ConfirmBookingRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class ConfirmBookingUseCase(UseCase[ConfirmBookingRequest, Booking]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    reminder_settings_repo: TrainerReminderSettingsRepository
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
            await _schedule_booking_jobs(
                booking_id=saved.id,
                trainer_id=booking.trainer_id,
                slot=slot,
                reminder_settings_repo=self.reminder_settings_repo,
                booking_scheduler=self.booking_scheduler,
                transaction_manager=self.transaction_manager,
            )

        return saved
