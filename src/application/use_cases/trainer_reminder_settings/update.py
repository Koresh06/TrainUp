from dataclasses import dataclass
from datetime import timedelta

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import REMINDER_HOURS_BEFORE_TRAINING, REMINDER_TEST_MODE
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.domain.utils import get_project_today, get_training_datetime_utc
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now


@dataclass(frozen=True, eq=False)
class UpdateTrainerReminderSettingsRequest(UseCaseRequest):
    trainer_id: int
    hours_before: int


@dataclass(kw_only=True)
class UpdateTrainerReminderSettingsUseCase(
    UseCase[UpdateTrainerReminderSettingsRequest, TrainerReminderSettings]
):
    settings_repo: TrainerReminderSettingsRepository
    booking_repo: BookingRepository
    slot_repo: CalendarSlotRepository
    booking_scheduler: BookingScheduler
    transaction_manager: TransactionManager

    async def __call__(
        self, command: UpdateTrainerReminderSettingsRequest
    ) -> TrainerReminderSettings:
        existing = await self.settings_repo.get_by_trainer_id(command.trainer_id)
        old_hours = (
            existing.hours_before if existing is not None else REMINDER_HOURS_BEFORE_TRAINING
        )
        if existing is not None:
            existing.hours_before = command.hours_before
            saved = await self.settings_repo.save(existing)
        else:
            saved = await self.settings_repo.save(
                TrainerReminderSettings(
                    trainer_id=command.trainer_id,
                    hours_before=command.hours_before,
                )
            )
        await self.transaction_manager.commit()

        if old_hours != command.hours_before and not REMINDER_TEST_MODE:
            await self._reschedule_upcoming(
                command.trainer_id, old_hours=old_hours, new_hours=command.hours_before
            )
        return saved

    async def _reschedule_upcoming(
        self, trainer_id: int, *, old_hours: int, new_hours: int
    ) -> None:
        """
        Напоминания уже подтверждённых записей (в т.ч. постоянок на неделю
        вперёд) стоят в планировщике со старым временем — без переноса новая
        настройка заработала бы только через неделю-две.

        Переносим, только если и старое, и новое время ещё впереди: старое уже
        прошло — клиент напоминание получил, второе не нужно; новое уже прошло —
        оставляем старое, а не шлём «прямо сейчас» всем подряд.
        """
        now = get_datetime_utc_now()
        views = await self.booking_repo.get_views(
            trainer_id=trainer_id,
            date_from=get_project_today(),
            statuses=(BookingStatus.CONFIRMED,),
        )
        for view in views:
            if not view.client_has_telegram:
                continue
            slot = await self.slot_repo.get_by_id(view.booking.slot_id)
            if slot is None:
                continue
            training_at = get_training_datetime_utc(slot)
            old_remind_at = training_at - timedelta(hours=old_hours)
            new_remind_at = training_at - timedelta(hours=new_hours)
            if old_remind_at <= now or new_remind_at <= now:
                continue
            await self.booking_scheduler.cancel_training_reminder(booking_id=view.booking.id)
            await self.booking_scheduler.schedule_training_reminder(
                booking_id=view.booking.id, remind_at_utc=new_remind_at
            )
        # BookingScheduler пишет job_id в бронь (flush) — без commit id теряются
        await self.transaction_manager.commit()
