"""Оценка тренировки клиентом после завершения."""

from datetime import time, timedelta, timezone

import pytest

from src.application.use_cases.booking.create_by_trainer import CreateBookingByTrainerRequest
from src.application.use_cases.booking.mark_completed import MarkBookingCompletedRequest
from src.application.use_cases.booking.rate import RateBookingRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesRequest
from src.application.use_cases.stats.get_trainer import GetTrainerStatsRequest
from src.application.use_cases.stats.period import StatsPeriod
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer_booking_settings.update import (
    UpdateTrainerBookingSettingsRequest,
)
from src.domain.exception.booking import BookingNotFoundException, BookingStatusTransitionException
from src.domain.utils import get_project_today

T10 = time(10, 0, tzinfo=timezone.utc)
T12 = time(12, 0, tzinfo=timezone.utc)


@pytest.fixture
async def world(run):
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    day = get_project_today() + timedelta(days=1)
    await run(SyncWeekdaySlotTemplatesRequest(trainer_id=trainer.id, weekday=day.weekday(), time_capacities={T10: 2, T12: 2}))
    slots = sorted(await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day)), key=lambda s: s.start_time)
    client = await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=trainer.id, first_name="Пётр", last_name=None, username=None,
            phone="+375291234567", age=30, sport_experience="none", answers={},
        )
    )
    return trainer, client, slots


async def test_rating_flow(run, world, notifications) -> None:
    trainer, client, slots = world
    booking = await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=slots[0].id))

    with pytest.raises(BookingStatusTransitionException):
        await run(RateBookingRequest(booking_id=booking.id, client_id=client.id, stars=5))

    await run(MarkBookingCompletedRequest(booking_id=booking.id))
    [request] = notifications.of("notify_rating_request")
    assert request.chat_id == client.tg_id and request.booking_id == booking.id

    with pytest.raises(BookingNotFoundException):
        await run(RateBookingRequest(booking_id=booking.id, client_id=client.id + 1, stars=5))
    await run(RateBookingRequest(booking_id=booking.id, client_id=client.id, stars=2))
    assert any("оценил тренировку" in t for c, t in notifications.of("send") if c == trainer.notification_chat_id)


async def test_rating_in_stats(run, world, session) -> None:
    from src.domain.enums.booking import BookingStatus
    from tests.factories import make_booking, make_slot

    trainer, client, _ = world
    for hour, stars in ((0, 5), (1, 4)):
        slot = await make_slot(session, trainer.id, get_project_today(), time(hour, 0))
        booking = await make_booking(session, client, slot, BookingStatus.COMPLETED)
        await run(RateBookingRequest(booking_id=booking.id, client_id=client.id, stars=stars))

    stats = await run(GetTrainerStatsRequest(trainer_id=trainer.id, period=StatsPeriod.TODAY))
    assert stats.rating_count == 2 and stats.rating_average == 4.5


async def test_no_rating_request_when_off_or_offline(run, world, notifications) -> None:
    trainer, client, slots = world
    offline = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Олег"))
    b1 = await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=offline.id, slot_id=slots[0].id))
    await run(MarkBookingCompletedRequest(booking_id=b1.id))

    await run(
        UpdateTrainerBookingSettingsRequest(
            trainer_id=trainer.id, calendar_horizon_days=14, max_active_bookings_per_client=1, ask_rating=False,
        )
    )
    b2 = await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=slots[1].id))
    await run(MarkBookingCompletedRequest(booking_id=b2.id))
    assert notifications.of("notify_rating_request") == []
