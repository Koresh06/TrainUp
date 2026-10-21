"""Абонементы: списание при завершении/неявке, уведомления об остатке, долги и оплаты."""

from datetime import time, timedelta, timezone
from decimal import Decimal

import pytest

from src.application.use_cases.booking.create_by_trainer import CreateBookingByTrainerRequest
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.booking.mark_attendance import MarkBookingAttendanceRequest
from src.application.use_cases.booking.mark_completed import MarkBookingCompletedRequest
from src.application.use_cases.booking.mark_paid import MarkBookingsPaidRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.package.create import CreateClientPackageRequest
from src.application.use_cases.package.get_balances import GetClientBalancesRequest
from src.application.use_cases.package.get_by_client import GetClientPackagesRequest
from src.application.use_cases.package.manage import ManageClientPackageRequest, PackageAction
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer_booking_settings.update import (
    UpdateTrainerBookingSettingsRequest,
)
from src.application.use_cases.trainer_pricing_rule.update import UpdateTrainerPricingRuleRequest
from src.domain.enums.booking import BookingStatus
from src.domain.enums.package import PackageStatus
from src.domain.utils import get_project_today

TIMES = [time(h, 0, tzinfo=timezone.utc) for h in (9, 10, 11, 12)]


@pytest.fixture
async def world(run):
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    await run(
        UpdateTrainerPricingRuleRequest(
            trainer_id=trainer.id, boundary_time=time(0, 0, tzinfo=timezone.utc),
            price_before=Decimal("40"), price_after=Decimal("40"), trainer_fee=None,
        )
    )
    day = get_project_today() + timedelta(days=1)
    await run(
        SyncWeekdaySlotTemplatesRequest(
            trainer_id=trainer.id, weekday=day.weekday(), time_capacities={t: 1 for t in TIMES}
        )
    )
    slots = await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))
    client = await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=trainer.id, first_name="Пётр", last_name=None,
            username=None, phone="+375291234567", age=30, sport_experience="none", answers={},
        )
    )
    bookings = [
        await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=s.id))
        for s in sorted(slots, key=lambda s: s.start_time)
    ]
    return {"trainer": trainer, "client": client, "bookings": bookings}


async def test_package_charging_and_notifications(run, world, notifications) -> None:
    trainer, client, bookings = world["trainer"], world["client"], world["bookings"]
    package = await run(
        CreateClientPackageRequest(
            trainer_id=trainer.id, client_id=client.id, sessions_total=2,
            price=Decimal("70"), valid_days=30, paid=False,
        )
    )
    assert package.title == "2 занятия" and package.valid_until is not None
    assert any("Абонемент «2 занятия»" in t for c, t in notifications.of("send") if c == client.tg_id)

    await run(MarkBookingCompletedRequest(booking_id=bookings[0].id))
    assert (await run(GetBookingByIdRequest(booking_id=bookings[0].id))).package_id == package.id
    assert any("осталось <b>1 занятие</b>" in t for _, t in notifications.of("send"))

    await run(MarkBookingCompletedRequest(booking_id=bookings[1].id))
    [stored] = await run(GetClientPackagesRequest(client_id=client.id))
    assert stored.status == PackageStatus.FINISHED and stored.remaining == 0
    assert any("закончился абонемент" in t for c, t in notifications.of("send") if c == trainer.notification_chat_id)

    # абонемент кончился — следующая тренировка разовая и не оплачена
    await run(MarkBookingCompletedRequest(booking_id=bookings[2].id))
    balance = (await run(GetClientBalancesRequest(trainer_id=trainer.id, client_id=client.id)))[client.id]
    assert [v.booking.id for v in balance.unpaid_bookings] == [bookings[2].id]
    assert balance.debt == Decimal("40") + Decimal("70")  # разовая + неоплаченный абонемент

    await run(MarkBookingsPaidRequest(trainer_id=trainer.id, booking_ids=(bookings[2].id,)))
    await run(ManageClientPackageRequest(trainer_id=trainer.id, package_id=package.id, action=PackageAction.MARK_PAID))
    balance = (await run(GetClientBalancesRequest(trainer_id=trainer.id, client_id=client.id)))[client.id]
    assert balance.debt == 0


async def test_no_show_charging_setting(run, world, session) -> None:
    from tests.factories import make_booking, make_slot

    trainer, client = world["trainer"], world["client"]
    package = await run(
        CreateClientPackageRequest(trainer_id=trainer.id, client_id=client.id, sessions_total=5, paid=True)
    )
    past_slot = await make_slot(session, trainer.id, get_project_today(), time(0, 0))
    past = await make_booking(session, client, past_slot, BookingStatus.CONFIRMED)

    # по умолчанию неявка списывает занятие
    await run(MarkBookingAttendanceRequest(trainer_id=trainer.id, booking_id=past.id, attended=False))
    [stored] = await run(GetClientPackagesRequest(client_id=client.id))
    assert stored.sessions_used == 1

    # тренер выключил списание за неявку — повторная отметка возвращает занятие
    await run(
        UpdateTrainerBookingSettingsRequest(
            trainer_id=trainer.id, calendar_horizon_days=14, max_active_bookings_per_client=1,
            no_show_charges_package=False,
        )
    )
    await run(MarkBookingAttendanceRequest(trainer_id=trainer.id, booking_id=past.id, attended=True))
    await run(MarkBookingAttendanceRequest(trainer_id=trainer.id, booking_id=past.id, attended=False))
    [stored] = await run(GetClientPackagesRequest(client_id=client.id))
    booking = await run(GetBookingByIdRequest(booking_id=past.id))
    assert stored.sessions_used == 0 and booking.package_id is None
    assert stored.id == package.id


async def test_cancelled_package_is_not_charged(run, world) -> None:
    trainer, client, bookings = world["trainer"], world["client"], world["bookings"]
    package = await run(
        CreateClientPackageRequest(trainer_id=trainer.id, client_id=client.id, sessions_total=4, paid=True)
    )
    await run(ManageClientPackageRequest(trainer_id=trainer.id, package_id=package.id, action=PackageAction.CANCEL))
    await run(MarkBookingCompletedRequest(booking_id=bookings[0].id))
    assert (await run(GetBookingByIdRequest(booking_id=bookings[0].id))).package_id is None
