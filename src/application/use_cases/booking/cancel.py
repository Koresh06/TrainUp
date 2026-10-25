from dataclasses import dataclass
from html import escape

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingActor
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.database.transaction_manager.base import TransactionManager


# кто отменил — сохраняется в записи (cancelled_by) и видно тренеру в истории
CancelInitiator = BookingActor


@dataclass(frozen=True, eq=False)
class CancelBookingRequest(UseCaseRequest):
    booking_id: int
    initiated_by: CancelInitiator = CancelInitiator.TRAINER
    # свой текст клиенту вместо стандартного (например, «тренер в отпуске»)
    client_message: str | None = None


@dataclass(kw_only=True)
class CancelBookingUseCase(UseCase[CancelBookingRequest, Booking]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    calendar_service: CalendarService
    notification_service: NotificationService
    booking_scheduler: BookingScheduler
    transaction_manager: TransactionManager

    async def __call__(self, command: CancelBookingRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None:
            raise BookingNotFoundException(command.booking_id)

        booking.cancel(by=command.initiated_by)
        await self.calendar_service.release_slot(booking.slot_id)
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        if booking.reminder_job_id:
            await self.booking_scheduler.cancel_training_reminder(booking_id=booking.id)

        if booking.completion_job_id:
            await self.booking_scheduler.cancel_booking_completion(booking_id=booking.id)
        await self.transaction_manager.commit()

        if command.initiated_by == CancelInitiator.TRAINER:
            trainer = await self.trainer_repo.get_by_id(booking.trainer_id)
            client = await self.client_repo.get_by_id(booking.client_id)
            slot = await self.slot_repo.get_by_id(booking.slot_id)
            # клиенту без Telegram сообщить некуда — тренер предупреждает сам
            if (
                trainer is not None
                and client is not None
                and client.has_telegram
                and slot is not None
            ):
                await self.notification_service.send(
                    chat_id=client.tg_id,
                    text=(
                        f"❌ Тренер {escape(trainer.name)} отменил вашу тренировку\n\n"
                        f"📅 {slot.slot_date.strftime('%d.%m.%Y')}\n"
                        f"🕐 {slot.start_time.strftime('%H:%M')}\n\n"
                        + (command.client_message or "Вы можете выбрать другое время.")
                    ),
                )
        elif command.initiated_by == CancelInitiator.CLIENT:
            trainer = await self.trainer_repo.get_by_id(booking.trainer_id)
            client = await self.client_repo.get_by_id(booking.client_id)
            slot = await self.slot_repo.get_by_id(booking.slot_id)
            if trainer is not None and client is not None and slot is not None:
                full_name = client.first_name
                if client.last_name:
                    full_name += f" {client.last_name}"
                username_line = (
                    f"@{client.username}"
                    if client.username
                    else f"tg_id: {client.tg_id}"
                )
                await self.notification_service.send(
                    chat_id=trainer.notification_chat_id,
                    fallback_chat_id=trainer.tg_id,
                    text=(
                        f"❌ Клиент {escape(full_name)} отменил тренировку\n\n"
                        f"👤 {username_line}\n"
                        f"📞 {client.phone or '—'}\n\n"
                        f"📅 {slot.slot_date.strftime('%d.%m.%Y')}\n"
                        f"🕐 {slot.start_time.strftime('%H:%M')}"
                    ),
                )

        return saved
