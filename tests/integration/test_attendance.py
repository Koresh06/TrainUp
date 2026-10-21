"""Запрос «придёте?» накануне и подтверждение явки клиентом."""

from datetime import datetime, time, timedelta, timezone

import pytest
from sqlalchemy import text

from src.application.use_cases.booking.attendance import (
    ConfirmAttendanceRequest,
    SendAttendanceRequestsRequest,
)
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.booking.reschedule import RescheduleBookingRequest
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer_booking_settings.update import (
    UpdateTrainerBookingSettingsRequest,
)
from src.domain.constants import PROJECT_TIMEZONE
from src.domain.enums.booking import BookingStatus
from src.domain.enums.subscription import SubscriptionSource
from src.domain.exception.booking import BookingNotFoundException
from src.domain.utils import get_project_today
from tests.factories import make_booking, make_slot


async def _booked_long_ago(session, client, slot):
    booking = await make_booking(session, client, slot, BookingStatus.CONFIRMED)
    await session.execute(
        text("UPDATE bookings SET created_at = now() - interval '3 days' WHERE id = :id"),
        {"id": booking.id},
    )
    await session.commit()
    return booking


def _training_at(day, hour: int) -> datetime:
    return datetime.combine(day, time(hour, 0), tzinfo=PROJECT_TIMEZONE).astimezone(timezone.utc)


@pytest.fixture
async def world(run, session):
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    await run(GrantSubscriptionRequest(trainer_id=trainer.id, source=SubscriptionSource.CASH, days=30))
    client = await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=trainer.id, first_name="Пётр", last_name=None,
            username=None, phone="+375291234567", age=30, sport_experience="none", answers={},
        )
    )
    day = get_project_today() + timedelta(days=1)
    slot = await make_slot(session, trainer.id, day, time(10, 0))
    other = await make_slot(session, trainer.id, day, time(12, 0))
    booking = await _booked_long_ago(session, client, slot)
    return {"trainer": trainer, "client": client, "booking": booking, "day": day, "other": other}


async def test_attendance_request_once_and_confirm(run, world, notifications) -> None:
    booking, client, day = world["booking"], world["client"], world["day"]
    now = _training_at(day, 10) - timedelta(hours=20)

    assert await run(SendAttendanceRequestsRequest(now=now)) == 1
    assert await run(SendAttendanceRequestsRequest(now=now + timedelta(minutes=30))) == 0
    [request] = notifications.of("notify_attendance_request")
    assert request.chat_id == client.tg_id and request.time_label == "10:00" and request.is_tomorrow

    with pytest.raises(BookingNotFoundException):
        await run(ConfirmAttendanceRequest(booking_id=booking.id, client_id=client.id + 100))
    await run(ConfirmAttendanceRequest(booking_id=booking.id, client_id=client.id))
    assert (await run(GetBookingByIdRequest(booking_id=booking.id))).client_confirmed_at is not None

    # перенос — подтверждение относилось к старому времени
    await run(RescheduleBookingRequest(booking_id=booking.id, new_slot_id=world["other"].id))
    moved = await run(GetBookingByIdRequest(booking_id=booking.id))
    assert moved.client_confirmed_at is None and moved.attendance_requested_at is None


async def test_attendance_request_skips(run, world, session) -> None:
    trainer, day = world["trainer"], world["day"]
    # слишком рано (больше суток) и уже в окне обычного напоминания (2 ч) — молчим
    assert await run(SendAttendanceRequestsRequest(now=_training_at(day, 10) - timedelta(hours=25))) == 0
    assert await run(SendAttendanceRequestsRequest(now=_training_at(day, 10) - timedelta(hours=1))) == 0

    # клиент без Telegram — спросить некого
    offline = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Олег"))
    late_slot = await make_slot(session, trainer.id, day, time(14, 0))
    await _booked_long_ago(session, offline, late_slot)

    # тренер выключил запросы
    await run(
        UpdateTrainerBookingSettingsRequest(
            trainer_id=trainer.id, calendar_horizon_days=14, max_active_bookings_per_client=1,
            ask_attendance_confirmation=False,
        )
    )
    assert await run(SendAttendanceRequestsRequest(now=_training_at(day, 10) - timedelta(hours=20))) == 0
