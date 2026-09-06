from dataclasses import dataclass
from enum import Enum

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.database.transaction_manager.base import TransactionManager


class CancelInitiator(str, Enum):
    TRAINER = "trainer"
    CLIENT = "client"


@dataclass(frozen=True, eq=False)
class CancelBookingRequest(UseCaseRequest):
    booking_id: int
    initiated_by: CancelInitiator = CancelInitiator.TRAINER


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

        booking.cancel()
        await self.calendar_service.release_slot(booking.slot_id)
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        if booking.reminder_job_id:
            await self.booking_scheduler.cancel_training_reminder(booking_id=booking.id)

        if command.initiated_by == CancelInitiator.TRAINER:
            client = await self.client_repo.get_by_id(booking.client_id)
            if client is not None:
                await self.notification_service.send(
                    chat_id=client.tg_id,
                    text="❌ Тренер отменил вашу запись. Вы можете выбрать другое время.",
                )
        else:
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
                    text=(
                        f"❌ Клиент {full_name} отменил тренировку\n\n"
                        f"👤 {username_line}\n"
                        f"📞 {client.phone}\n\n"
                        f"📅 {slot.slot_date.strftime('%d.%m.%Y')}\n"
                        f"🕐 {slot.start_time.strftime('%H:%M')}"
                    ),
                )

        return saved
