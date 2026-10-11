"""Сквозные сценарии записи: use case'ы через Mediator на реальной БД."""

from datetime import time, timedelta, timezone
from decimal import Decimal

import pytest

from src.application.use_cases.booking.cancel import CancelBookingRequest, CancelInitiator
from src.application.use_cases.booking.confirm import ConfirmBookingRequest
from src.application.use_cases.booking.create import CreateBookingRequest
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.booking.get_upcoming_by_client import (
    GetUpcomingBookingsByClientRequest,
)
from src.application.use_cases.booking.mark_completed import MarkBookingCompletedRequest
from src.application.use_cases.booking.reschedule import RescheduleBookingRequest
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
)
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.calendar.set_day_blocked import SetDayBlockedRequest
from src.application.use_cases.calendar.set_slot_blocked import SetSlotBlockedRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.registration_questions.get_active import (
    GetActiveRegistrationQuestionsRequest,
)
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesRequest,
)
from src.application.use_cases.stats.get_trainer import GetTrainerStatsRequest
from src.application.use_cases.stats.period import StatsPeriod
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer_pricing_rule.update import (
    UpdateTrainerPricingRuleRequest,
)
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import (
    ActiveBookingsLimitExceededException,
    BookingStatusTransitionException,
)
from src.domain.utils import get_project_today

T10 = time(10, 0, tzinfo=timezone.utc)
T12 = time(12, 0, tzinfo=timezone.utc)


@pytest.fixture
async def world(run):
    """Тренер с ценами и расписанием на завтра (10:00 ×2 места, 12:00 ×1) и клиент."""
    trainer = await run(
        RegisterTrainerRequest(tg_id=1001, name="Иван", bio="bio", notification_chat_id=-1)
    )
    await run(
        UpdateTrainerPricingRuleRequest(
            trainer_id=trainer.id, boundary_time=time(11, 0, tzinfo=timezone.utc),
            price_before=Decimal("20"), price_after=Decimal("30"), trainer_fee=None,
        )
    )
    tomorrow = get_project_today() + timedelta(days=1)
    await run(
        SyncWeekdaySlotTemplatesRequest(
            trainer_id=trainer.id, weekday=tomorrow.weekday(), time_capacities={T10: 2, T12: 1}
        )
    )
    questions = await run(GetActiveRegistrationQuestionsRequest(trainer_id=trainer.id))
    client = await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=trainer.id, first_name="Пётр", last_name=None,
            username="petr", phone="+375291234567", age=30, sport_experience="none",
            answers={str(questions[0].id): ["Другое: старая травма колена"]},
        )
    )
    slots = await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=tomorrow))
    by_time = {s.start_time: s for s in slots}
    return {"trainer": trainer, "client": client, "day": tomorrow, "s10": by_time[T10], "s12": by_time[T12]}


async def test_booking_lifecycle(run, world, notifications, task_queue) -> None:
    trainer, client, s10, s12 = world["trainer"], world["client"], world["s10"], world["s12"]

    booking = await run(CreateBookingRequest(client_id=client.id, trainer_id=trainer.id, slot_id=s10.id))
    stored = await run(GetBookingByIdRequest(booking_id=booking.id))
    assert stored.price == Decimal("20")
    [new_booking] = notifications.of("notify_new_booking")
    assert ("Ваше состояние здоровья и тела", "Другое: старая травма колена") in new_booking.client_answers

    with pytest.raises(ActiveBookingsLimitExceededException):
        await run(CreateBookingRequest(client_id=client.id, trainer_id=trainer.id, slot_id=s12.id))

    await run(ConfirmBookingRequest(booking_id=booking.id))
    stored = await run(GetBookingByIdRequest(booking_id=booking.id))
    assert stored.reminder_job_id and stored.completion_job_id
    with pytest.raises(BookingStatusTransitionException):
        await run(ConfirmBookingRequest(booking_id=booking.id))

    await run(RescheduleBookingRequest(booking_id=booking.id, new_slot_id=s12.id))
    moved = await run(GetBookingByIdRequest(booking_id=booking.id))
    assert moved.slot_id == s12.id and moved.price == Decimal("30")
    assert moved.completion_job_id != stored.completion_job_id

    await run(CancelBookingRequest(booking_id=booking.id, initiated_by=CancelInitiator.CLIENT))
    with pytest.raises(BookingStatusTransitionException):
        await run(CancelBookingRequest(booking_id=booking.id))

    stats = await run(GetTrainerStatsRequest(trainer_id=trainer.id, period=StatsPeriod.TODAY))
    assert stats.cancelled_bookings == 1


async def test_completion_schedules_plan_next_reminder(run, world, task_queue) -> None:
    booking = await run(
        CreateBookingRequest(client_id=world["client"].id, trainer_id=world["trainer"].id, slot_id=world["s10"].id)
    )
    await run(ConfirmBookingRequest(booking_id=booking.id))
    await run(MarkBookingCompletedRequest(booking_id=booking.id))

    assert (await run(GetBookingByIdRequest(booking_id=booking.id))).status == BookingStatus.COMPLETED
    assert [t for t, *_ in task_queue.scheduled].count("send_plan_next_training_reminder") == 1


async def test_schedule_changes_and_blocking(run, world) -> None:
    trainer, day, s10 = world["trainer"], world["day"], world["s10"]

    # убрали 12:00 из шаблона → слот скрыт
    await run(SyncWeekdaySlotTemplatesRequest(trainer_id=trainer.id, weekday=day.weekday(), time_capacities={T10: 2}))
    assert [s.start_time for s in await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))] == [T10]
    # вернули → снова доступен (раньше оставался заблокированным навсегда)
    await run(SyncWeekdaySlotTemplatesRequest(trainer_id=trainer.id, weekday=day.weekday(), time_capacities={T10: 2, T12: 1}))
    assert len(await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))) == 2

    await run(SetSlotBlockedRequest(slot_id=s10.id, blocked=True))
    availability = await run(GetDayAvailabilityMapRequest(trainer_id=trainer.id, days_ahead=14))
    assert availability.get(day) == 1  # осталось только 12:00

    changed = await run(SetDayBlockedRequest(trainer_id=trainer.id, slot_date=day, blocked=True))
    assert changed == 1
    assert day not in await run(GetDayAvailabilityMapRequest(trainer_id=trainer.id, days_ahead=14))

    await run(SetDayBlockedRequest(trainer_id=trainer.id, slot_date=day, blocked=False))
    availability = await run(GetDayAvailabilityMapRequest(trainer_id=trainer.id, days_ahead=14))
    assert availability.get(day) == 3

    upcoming = await run(GetUpcomingBookingsByClientRequest(client_id=world["client"].id))
    assert upcoming == []
