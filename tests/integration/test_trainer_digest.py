"""Утренняя/вечерняя сводка тренеру: час из настроек, без дублей, только с подпиской."""

from datetime import datetime, time, timedelta

import pytest

from src.application.use_cases.booking.create_by_trainer import CreateBookingByTrainerRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.digest.send_trainer_digests import SendTrainerDigestsRequest
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesRequest
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer_reminder_settings.update_digest import (
    UpdateTrainerDigestSettingsRequest,
)
from src.domain.constants import PROJECT_TIMEZONE
from src.domain.enums.subscription import SubscriptionSource
from src.domain.utils import get_project_today

T10 = time(10, 0)


def at(day, hour: int) -> datetime:
    return datetime.combine(day, time(hour, 5), tzinfo=PROJECT_TIMEZONE)


@pytest.fixture
async def trainer_with_tomorrow_training(run):
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    await run(GrantSubscriptionRequest(trainer_id=trainer.id, source=SubscriptionSource.CASH, days=30))
    tomorrow = get_project_today() + timedelta(days=1)
    from datetime import timezone
    await run(
        SyncWeekdaySlotTemplatesRequest(
            trainer_id=trainer.id, weekday=tomorrow.weekday(),
            time_capacities={T10.replace(tzinfo=timezone.utc): 1},
        )
    )
    [slot] = await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=tomorrow))
    client = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Олег", trainer_note="колено"))
    await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=slot.id))
    return trainer, tomorrow


async def test_morning_digest_once_per_day(run, trainer_with_tomorrow_training, notifications) -> None:
    trainer, tomorrow = trainer_with_tomorrow_training

    # по умолчанию — 8:00; не в тот час ничего не уходит
    assert await run(SendTrainerDigestsRequest(now=at(tomorrow, 7))) == 0
    assert await run(SendTrainerDigestsRequest(now=at(tomorrow, 8))) == 1
    assert await run(SendTrainerDigestsRequest(now=at(tomorrow, 8))) == 0  # повторный запуск cron

    [digest] = notifications.of("notify_trainer_digest")
    assert digest.chat_id == trainer.tg_id and not digest.is_tomorrow
    [item] = digest.items
    assert item.client_name == "Олег" and item.is_offline and item.trainer_note == "колено"


async def test_evening_digest_and_empty_days(run, trainer_with_tomorrow_training, notifications) -> None:
    trainer, tomorrow = trainer_with_tomorrow_training
    today = get_project_today()
    await run(
        UpdateTrainerDigestSettingsRequest(
            trainer_id=trainer.id, morning_digest_hour=None, evening_digest_hour=20,
            digest_on_empty_days=False,
        )
    )
    assert await run(SendTrainerDigestsRequest(now=at(today, 8))) == 0  # утренняя выключена
    assert await run(SendTrainerDigestsRequest(now=at(today, 20))) == 1
    [digest] = notifications.of("notify_trainer_digest")
    assert digest.is_tomorrow and digest.day == tomorrow

    # послезавтра пусто: без «присылать в свободные дни» — молчим
    assert await run(SendTrainerDigestsRequest(now=at(tomorrow, 20))) == 0
    await run(
        UpdateTrainerDigestSettingsRequest(
            trainer_id=trainer.id, morning_digest_hour=None, evening_digest_hour=21,
            digest_on_empty_days=True,
        )
    )
    assert await run(SendTrainerDigestsRequest(now=at(tomorrow + timedelta(days=1), 21))) == 1


async def test_no_digest_without_subscription(run, notifications) -> None:
    await run(RegisterTrainerRequest(tg_id=1002, name="Без подписки", bio="", notification_chat_id=-2))
    await run(
        UpdateTrainerDigestSettingsRequest(
            trainer_id=1, morning_digest_hour=8, evening_digest_hour=None, digest_on_empty_days=True,
        )
    )
    assert await run(SendTrainerDigestsRequest(now=at(get_project_today(), 8))) == 0
