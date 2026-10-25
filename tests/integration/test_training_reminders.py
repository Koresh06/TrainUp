"""Напоминания клиенту о тренировке и надёжность уведомлений."""

from datetime import datetime, time, timedelta

import pytest

from src.application.use_cases.booking.cancel import CancelBookingRequest, CancelInitiator
from src.application.use_cases.booking.create_by_trainer import CreateBookingByTrainerRequest
from src.application.use_cases.booking.mark_completed import MarkBookingCompletedRequest
from src.application.use_cases.booking.rate import RateBookingRequest
from src.application.use_cases.booking.send_reminder import SendTrainingReminderRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.client.set_blocked import SetClientBlockedRequest
from src.application.use_cases.digest.send_trainer_digests import SendTrainerDigestsRequest
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer_reminder_settings.update import (
    UpdateTrainerReminderSettingsRequest,
)
from src.domain.constants import PROJECT_TIMEZONE
from src.domain.enums.subscription import SubscriptionSource
from src.domain.utils import get_project_today, get_training_datetime_utc
from tests.factories import make_slot


@pytest.fixture
async def world(run, session):
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    await run(GrantSubscriptionRequest(trainer_id=trainer.id, source=SubscriptionSource.CASH, days=30))
    client = await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=trainer.id, first_name="<Пётр>", last_name=None,
            username=None, phone="+375291234567", age=30, sport_experience="none", answers={},
        )
    )
    slot = await make_slot(session, trainer.id, get_project_today() + timedelta(days=3), time(10, 0))
    booking = await run(
        CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=slot.id)
    )
    return {"trainer": trainer, "client": client, "slot": slot, "booking": booking}


def _reminders(task_queue, booking_id: int) -> list[datetime]:
    return [
        run_at for name, args, run_at in task_queue.scheduled
        if name == "send_training_reminder" and args == (booking_id,)
    ]


async def test_reminder_scheduled_by_trainer_setting(world, task_queue) -> None:
    training_at = get_training_datetime_utc(world["slot"])
    assert _reminders(task_queue, world["booking"].id) == [training_at - timedelta(hours=2)]


async def test_changing_hours_reschedules_upcoming(run, world, task_queue) -> None:
    trainer, booking = world["trainer"], world["booking"]
    training_at = get_training_datetime_utc(world["slot"])

    await run(UpdateTrainerReminderSettingsRequest(trainer_id=trainer.id, hours_before=24))
    assert _reminders(task_queue, booking.id)[-1] == training_at - timedelta(hours=24)

    # то же значение повторно — ничего не перепланируем
    before = len(task_queue.scheduled)
    await run(UpdateTrainerReminderSettingsRequest(trainer_id=trainer.id, hours_before=24))
    assert len(task_queue.scheduled) == before


async def test_no_second_reminder_when_old_one_already_sent(run, world, task_queue, monkeypatch) -> None:
    trainer = world["trainer"]
    training_at = get_training_datetime_utc(world["slot"])
    await run(UpdateTrainerReminderSettingsRequest(trainer_id=trainer.id, hours_before=24))

    # за 10 ч до тренировки: напоминание «за 24 ч» уже ушло — «за 2 ч» не дублируем
    monkeypatch.setattr(
        "src.application.use_cases.trainer_reminder_settings.update.get_datetime_utc_now",
        lambda: training_at - timedelta(hours=10),
    )
    before = len(task_queue.scheduled)
    await run(UpdateTrainerReminderSettingsRequest(trainer_id=trainer.id, hours_before=2))
    assert len(task_queue.scheduled) == before


async def test_reminder_sent_to_active_client_only(run, world, notifications) -> None:
    booking, client = world["booking"], world["client"]
    await run(SendTrainingReminderRequest(booking_id=booking.id))
    [reminder] = notifications.of("notify_training_reminder")
    assert reminder.chat_id == client.tg_id and reminder.minutes_before > 0

    await run(SetClientBlockedRequest(client_id=client.id, blocked=True))
    await run(SendTrainingReminderRequest(booking_id=booking.id))
    assert len(notifications.of("notify_training_reminder")) == 1


async def test_late_reminder_after_start_is_skipped(run, world, notifications, monkeypatch) -> None:
    training_at = get_training_datetime_utc(world["slot"])
    monkeypatch.setattr(
        "src.application.use_cases.booking.send_reminder.get_datetime_utc_now",
        lambda: training_at + timedelta(minutes=5),
    )
    await run(SendTrainingReminderRequest(booking_id=world["booking"].id))
    assert notifications.of("notify_training_reminder") == []


async def test_client_name_escaped_in_trainer_notifications(run, world, notifications) -> None:
    trainer, booking, client = world["trainer"], world["booking"], world["client"]
    await run(MarkBookingCompletedRequest(booking_id=booking.id))
    await run(RateBookingRequest(booking_id=booking.id, client_id=client.id, stars=1))
    [(_, text)] = [s for s in notifications.of("send") if s[0] == trainer.notification_chat_id]
    # HTML-режим: «<» в имени роняет отправку целиком, а «\n» должен быть переводом строки
    assert "&lt;Пётр&gt;" in text and "\\n" not in text and "\n" in text


async def test_client_cancel_notifies_trainer_with_escaped_name(run, world, notifications) -> None:
    trainer, booking = world["trainer"], world["booking"]
    await run(CancelBookingRequest(booking_id=booking.id, initiated_by=CancelInitiator.CLIENT))
    [(_, text)] = [s for s in notifications.of("send") if s[0] == trainer.notification_chat_id]
    assert "&lt;Пётр&gt;" in text


async def test_digest_failure_for_one_trainer_does_not_stop_others(run, world, notifications) -> None:
    other = await run(RegisterTrainerRequest(tg_id=1002, name="Анна", bio="", notification_chat_id=-2))
    await run(GrantSubscriptionRequest(trainer_id=other.id, source=SubscriptionSource.CASH, days=30))
    first_id = world["trainer"].tg_id

    original = notifications.notify_trainer_digest

    async def flaky(data) -> None:
        if data.chat_id == first_id:
            raise RuntimeError("telegram flood")
        await original(data)

    notifications.notify_trainer_digest = flaky
    # тренировки только у первого — второму нужна сводка и в пустой день
    from src.application.use_cases.trainer_reminder_settings.update_digest import (
        UpdateTrainerDigestSettingsRequest,
    )
    await run(
        UpdateTrainerDigestSettingsRequest(
            trainer_id=other.id, morning_digest_hour=8, evening_digest_hour=None,
            digest_on_empty_days=True,
        )
    )
    now = datetime.combine(world["slot"].slot_date, time(8, 5), tzinfo=PROJECT_TIMEZONE)
    assert await run(SendTrainerDigestsRequest(now=now)) == 1
    [digest] = notifications.of("notify_trainer_digest")
    assert digest.chat_id == other.tg_id
