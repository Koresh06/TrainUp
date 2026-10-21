import logging
from dataclasses import dataclass
from datetime import timedelta

from src.application.interfaces.notification_service import (
    NotificationService,
    PlanNextTrainingNotificationDTO,
)
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import PLAN_NEXT_TRAINING_REMINDER_DAYS
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.utils import get_training_datetime_utc
from src.utils.get_datetime_utc_now import get_datetime_utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SendPlanNextTrainingReminderRequest(UseCaseRequest):
    client_id: int


@dataclass(kw_only=True)
class SendPlanNextTrainingReminderUseCase(
    UseCase[SendPlanNextTrainingReminderRequest, None]
):
    """
    Напоминание «запланируйте следующую тренировку». Ставится на
    PLAN_NEXT_TRAINING_REMINDER_DAYS дней вперёд после каждой завершённой
    тренировки; в момент срабатывания перепроверяем, актуально ли оно.
    """

    booking_repo: BookingRepository
    slot_repo: CalendarSlotRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    recurring_repo: RecurringBookingRepository
    notification_service: NotificationService

    async def __call__(self, command: SendPlanNextTrainingReminderRequest) -> None:
        client = await self.client_repo.get_by_id(command.client_id)
        if client is None or not client.is_active or not client.has_telegram:
            return

        upcoming = await self.booking_repo.get_upcoming_by_client(client.id)
        if upcoming:
            logger.info("[PlanNextReminder:skip] client_id=%s has upcoming", client.id)
            return

        recurring = await self.recurring_repo.get_active_by_trainer_and_client(
            trainer_id=client.trainer_id, client_id=client.id
        )
        if recurring:
            logger.info("[PlanNextReminder:skip] client_id=%s is recurring", client.id)
            return

        # после этой тренировки была ещё одна — по ней запланировано своё,
        # более позднее напоминание, это пропускаем, чтобы не дублировать
        latest = await self.booking_repo.get_latest_completed_by_client(client.id)
        if latest is None:
            return
        latest_slot = await self.slot_repo.get_by_id(latest.slot_id)
        if latest_slot is None:
            return
        since_training = get_datetime_utc_now() - get_training_datetime_utc(latest_slot)
        if since_training < timedelta(days=PLAN_NEXT_TRAINING_REMINDER_DAYS) - timedelta(hours=1):
            logger.info("[PlanNextReminder:skip] client_id=%s newer training", client.id)
            return

        trainer = await self.trainer_repo.get_by_id(client.trainer_id)
        if trainer is None:
            return

        await self.notification_service.notify_plan_next_training(
            PlanNextTrainingNotificationDTO(
                chat_id=client.tg_id,
                trainer_name=trainer.name,
                days_since_training=since_training.days,
            )
        )
        logger.info("[PlanNextReminder:done] client_id=%s", client.id)
