from datetime import timedelta

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.domain.constants import (
    REMINDER_HOURS_BEFORE_TRAINING,
    REMINDER_TEST_DELAY_MINUTES,
    REMINDER_TEST_MODE,
    SLOT_DURATION_MINUTES,
)
from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.repositories.trainer_reminder_settings import TrainerReminderSettingsRepository
from src.domain.services.calendar_service import CalendarService
from src.domain.utils import get_training_datetime_utc
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now


async def _create_recurring_occurrence(
    *,
    recurring: RecurringBooking,
    slot: CalendarSlot,
    booking_repo: BookingRepository,
    calendar_service: CalendarService,
    pricing_rule_repo: TrainerPricingRuleRepository,
    reminder_settings_repo: TrainerReminderSettingsRepository,
    client_repo: ClientRepository,
    trainer_repo: TrainerRepository,
    notification_service: NotificationService,
    booking_scheduler: BookingScheduler,
    transaction_manager: TransactionManager,
) -> Booking:
    await calendar_service.book_slot_forced(slot.id)

    pricing_rule = await pricing_rule_repo.get_by_trainer_id(recurring.trainer_id)
    price = (
        pricing_rule.price_for(slot.start_time) if pricing_rule is not None else None
    )

    booking = Booking(
        client_id=recurring.client_id,
        trainer_id=recurring.trainer_id,
        slot_id=slot.id,
        status=BookingStatus.CONFIRMED,
        price=price,
        recurring_booking_id=recurring.id,
    )
    saved = await booking_repo.save(booking)
    await transaction_manager.commit()

    client = await client_repo.get_by_id(recurring.client_id)
    trainer = await trainer_repo.get_by_id(recurring.trainer_id)
    if client is not None and trainer is not None:
        contact_lines = [
            f'💬 <a href="tg://user?id={trainer.tg_id}">Написать тренеру в Telegram</a>'
        ]
        if trainer.phone:
            contact_lines.append(f"📞 {trainer.phone}")
        contact_block = "\n".join(contact_lines)

        text = (
            f"📅 <b>Ваша постоянная тренировка запланирована</b>\n\n"
            f"Тренер: {trainer.name}\n"
            f"📅 {slot.slot_date.strftime('%d.%m.%Y')}\n"
            f"🕐 {slot.start_time.strftime('%H:%M')}\n\n"
            f"Если понадобится перенести время — свяжитесь с тренером напрямую:\n"
            f"{contact_block}"
        )
        await notification_service.send(chat_id=client.tg_id, text=text)

    reminder_settings = await reminder_settings_repo.get_by_trainer_id(
        recurring.trainer_id
    )
    hours_before = (
        reminder_settings.hours_before
        if reminder_settings is not None
        else REMINDER_HOURS_BEFORE_TRAINING
    )

    if REMINDER_TEST_MODE:
        remind_at_utc = get_datetime_utc_now() + timedelta(
            minutes=REMINDER_TEST_DELAY_MINUTES
        )
    else:
        training_at_utc = get_training_datetime_utc(slot)
        remind_at_utc = training_at_utc - timedelta(hours=hours_before)

    if remind_at_utc > get_datetime_utc_now():
        await booking_scheduler.schedule_training_reminder(
            booking_id=saved.id,
            remind_at_utc=remind_at_utc,
        )

    complete_at_utc = get_training_datetime_utc(slot) + timedelta(
        minutes=SLOT_DURATION_MINUTES
    )
    await booking_scheduler.schedule_booking_completion(
        booking_id=saved.id,
        complete_at_utc=complete_at_utc,
    )

    return saved
