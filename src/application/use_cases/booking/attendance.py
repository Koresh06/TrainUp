import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.application.interfaces.notification_service import (
    AttendanceRequestDTO,
    NotificationService,
)
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import PROJECT_TIMEZONE, day_label
from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository, BookingView
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.domain.constants import REMINDER_HOURS_BEFORE_TRAINING
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_aware_utc_now

logger = logging.getLogger(__name__)

# за сколько до тренировки спрашиваем «придёте?»
ATTENDANCE_REQUEST_BEFORE = timedelta(hours=24)


def _training_at(view: BookingView) -> datetime:
    local = datetime.combine(view.slot_date, view.start_time.replace(tzinfo=None))
    return local.replace(tzinfo=PROJECT_TIMEZONE).astimezone(timezone.utc)


@dataclass(frozen=True, eq=False)
class SendAttendanceRequestsRequest(UseCaseRequest):
    now: datetime | None = None


@dataclass(kw_only=True)
class SendAttendanceRequestsUseCase(UseCase[SendAttendanceRequestsRequest, int]):
    """
    Накануне спрашиваем клиента «придёте?»: ✅ — тренер видит 👍 в расписании,
    ❌ — запись отменяется и время освобождается. Только для записей, сделанных
    заранее (за сутки и больше), — того, кто записался на сегодня, спрашивать
    странно; и не в окне обычного напоминания — оно и так спросит.
    """

    trainer_repo: TrainerRepository
    subscription_repo: TrainerSubscriptionRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    reminder_settings_repo: TrainerReminderSettingsRepository
    booking_repo: BookingRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: SendAttendanceRequestsRequest) -> int:
        now = command.now or get_aware_utc_now()
        today = now.astimezone(PROJECT_TIMEZONE).date()
        sent = 0

        for trainer in await self.trainer_repo.get_all_active():
            settings = await self.booking_settings_repo.get_by_trainer_id(trainer.id)
            if settings is not None and not settings.ask_attendance_confirmation:
                continue
            if await self.subscription_repo.get_active_by_trainer_id(trainer.id) is None:
                continue
            reminder = await self.reminder_settings_repo.get_by_trainer_id(trainer.id)
            reminder_window = timedelta(
                hours=reminder.hours_before if reminder else REMINDER_HOURS_BEFORE_TRAINING
            )

            views = await self.booking_repo.get_views(
                trainer_id=trainer.id,
                date_from=today,
                date_to=today + timedelta(days=1),
                statuses=(BookingStatus.CONFIRMED,),
            )
            for view in views:
                booking = view.booking
                training_at = _training_at(view)
                created_at = booking.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if (
                    not view.client_has_telegram
                    or booking.client_confirmed_at is not None
                    or booking.attendance_requested_at is not None
                    or not (now + reminder_window < training_at <= now + ATTENDANCE_REQUEST_BEFORE)
                    or training_at - created_at < ATTENDANCE_REQUEST_BEFORE
                ):
                    continue

                client = await self.client_repo.get_by_id(booking.client_id)
                if client is None or not client.has_telegram:
                    continue
                await self.notification_service.notify_attendance_request(
                    AttendanceRequestDTO(
                        chat_id=client.tg_id,
                        booking_id=booking.id,
                        trainer_name=trainer.name,
                        day_label=day_label(view.slot_date),
                        time_label=view.start_time.strftime("%H:%M"),
                        is_tomorrow=view.slot_date > today,
                    )
                )
                booking.attendance_requested_at = now
                await self.booking_repo.save(booking)
                await self.transaction_manager.commit()
                sent += 1

        logger.info("[SendAttendanceRequests:done] sent=%s", sent)
        return sent


@dataclass(frozen=True, eq=False)
class ConfirmAttendanceRequest(UseCaseRequest):
    booking_id: int
    client_id: int


@dataclass(kw_only=True)
class ConfirmAttendanceUseCase(UseCase[ConfirmAttendanceRequest, Booking]):
    """Клиент нажал «✅ Приду» — в запросе накануне или в напоминании."""

    booking_repo: BookingRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: ConfirmAttendanceRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None or booking.client_id != command.client_id:
            raise BookingNotFoundException(command.booking_id)
        booking.confirm_attendance()
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()
        return saved
