
from dataclasses import dataclass
import logging

from src.application.interfaces.notification_service import NotificationService, TrainingReminderNotificationDTO
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository


logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SendTrainingReminderRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class SendTrainingReminderUseCase(UseCase[SendTrainingReminderRequest, None]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    notification_service: NotificationService

    async def __call__(self, command: SendTrainingReminderRequest) -> None:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None or booking.status != BookingStatus.CONFIRMED:
            logger.info(
                "[SendTrainingReminder:skip] booking_id=%s not found or not confirmed",
                command.booking_id,
            )
            return

        client = await self.client_repo.get_by_id(booking.client_id)
        trainer = await self.trainer_repo.get_by_id(booking.trainer_id)
        slot = await self.slot_repo.get_by_id(booking.slot_id)

        if client is None or trainer is None or slot is None:
            logger.warning(
                "[SendTrainingReminder:skip] booking_id=%s missing related entity",
                command.booking_id,
            )
            return

        await self.notification_service.notify_training_reminder(
            TrainingReminderNotificationDTO(
                chat_id=client.tg_id,
                date_label=slot.slot_date.strftime("%d.%m.%Y"),
                time_label=slot.start_time.strftime("%H:%M"),
                trainer_name=trainer.name,
            )
        )
        logger.info("[SendTrainingReminder:done] booking_id=%s", command.booking_id)