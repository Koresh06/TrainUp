from datetime import timedelta

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.domain.constants import (
    REMINDER_HOURS_BEFORE_TRAINING,
    REMINDER_TEST_DELAY_MINUTES,
    REMINDER_TEST_MODE,
    SLOT_DURATION_MINUTES,
)
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.domain.utils import get_training_datetime_utc
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now


async def _schedule_booking_jobs(
    *,
    booking_id: int,
    trainer_id: int,
    slot: CalendarSlot,
    reminder_settings_repo: TrainerReminderSettingsRepository,
    booking_scheduler: BookingScheduler,
    transaction_manager: TransactionManager,
    send_reminder: bool = True,
) -> None:
    """
    Единая точка планирования отложенных задач подтверждённой брони:
    напоминание клиенту (за hours_before из настроек тренера) и автозавершение
    после окончания тренировки. Используется при подтверждении, переносе и
    создании тренировок постоянного клиента — чтобы правила не расходились.

    BookingScheduler пишет job_id в бронь (flush), поэтому в конце обязателен
    commit — иначе id задач теряются и их потом невозможно отменить.

    send_reminder=False — клиенту без Telegram напоминать некуда, ставим
    только автозавершение.
    """
    reminder_settings = await reminder_settings_repo.get_by_trainer_id(trainer_id)
    hours_before = (
        reminder_settings.hours_before
        if reminder_settings is not None
        else REMINDER_HOURS_BEFORE_TRAINING
    )
    training_at_utc = get_training_datetime_utc(slot)
    now = get_datetime_utc_now()

    if REMINDER_TEST_MODE:
        remind_at_utc = now + timedelta(minutes=REMINDER_TEST_DELAY_MINUTES)
    else:
        remind_at_utc = training_at_utc - timedelta(hours=hours_before)

    if not send_reminder:
        pass
    elif remind_at_utc > now:
        await booking_scheduler.schedule_training_reminder(
            booking_id=booking_id,
            remind_at_utc=remind_at_utc,
        )
    elif training_at_utc > now:
        # подтвердили уже внутри окна напоминания — шлём сразу
        await booking_scheduler.schedule_training_reminder(
            booking_id=booking_id,
            remind_at_utc=now + timedelta(seconds=10),
        )

    complete_at_utc = training_at_utc + timedelta(minutes=SLOT_DURATION_MINUTES)
    await booking_scheduler.schedule_booking_completion(
        booking_id=booking_id,
        complete_at_utc=complete_at_utc,
    )
    await transaction_manager.commit()
