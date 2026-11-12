from datetime import time, timedelta, timezone

import pytest
from decimal import Decimal

from src.application.use_cases.access.get_user_access import GetUserAccessRequest
from src.application.use_cases.admin.export_report import ExportReportRequest, ReportKind
from src.application.use_cases.admin.get_overview_stats import GetAdminOverviewStatsRequest
from src.application.use_cases.admin.get_trainer_report import GetAdminTrainerReportRequest
from src.application.use_cases.booking.get_upcoming_by_client import (
    GetUpcomingBookingsByClientRequest,
)
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.client.set_blocked import SetClientBlockedRequest
from src.application.use_cases.client_request.create_feedback import CreateFeedbackRequest
from src.application.use_cases.client_request.create_program import (
    CreateProgramRequestRequest,
)
from src.application.use_cases.client_request.get_by_trainer import (
    GetClientRequestsByTrainerRequest,
)
from src.application.use_cases.client_request.update_status import (
    UpdateClientRequestStatusRequest,
)
from src.application.use_cases.faq.get_active import GetActiveFaqItemsRequest
from src.application.use_cases.recurring_booking.add import AddRecurringBookingRequest
from src.application.use_cases.booking.cancel import CancelBookingRequest
from src.application.use_cases.calendar.set_slot_blocked import SetSlotBlockedRequest
from src.application.use_cases.recurring_booking.change import (
    ChangeRecurringBookingScheduleRequest,
)
from src.application.use_cases.recurring_booking.get_active_by_client import (
    GetActiveRecurringBookingsByClientRequest,
)
from src.application.use_cases.recurring_booking.deactivate import (
    DeactivateRecurringBookingRequest,
)
from src.application.use_cases.recurring_booking.maintain import (
    MaintainRecurringBookingsRequest,
)
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesRequest,
)
from src.application.use_cases.stats.period import StatsPeriod
from src.application.use_cases.subscription.check_expiring import (
    CheckExpiringSubscriptionsRequest,
)
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer.set_blocked import SetTrainerBlockedRequest
from src.domain.enums.booking import BookingStatus
from src.domain.enums.faq import FaqAudience
from src.domain.exception.booking import SlotAlreadyBookedException
from src.domain.exception.recurring_booking import RecurringBookingAlreadyExistsException
from src.domain.enums.program import ProgramType
from src.domain.enums.request import ClientRequestKind, RequestStatus
from src.domain.enums.subscription import SubscriptionSource
from src.domain.enums.training import TrainingDirection
from src.domain.utils import get_project_today
from src.infrastructure.database.seed import seed_faq_items

T10 = time(10, 0, tzinfo=timezone.utc)


async def _trainer_and_client(run, trainer_tg=1001, client_tg=2002):
    trainer = await run(
        RegisterTrainerRequest(tg_id=trainer_tg, name=f"Тренер {trainer_tg}", bio="", notification_chat_id=-1)
    )
    client = await run(
        RegisterClientRequest(
            tg_id=client_tg, trainer_id=trainer.id, first_name="Анна", last_name=None,
            username=None, phone="+375291234567", age=25, sport_experience="none", answers={},
        )
    )
    return trainer, client


async def test_stop_recurring_cancels_future_trainings(run, notifications) -> None:
    trainer, client = await _trainer_and_client(run)
    day = get_project_today() + timedelta(days=1)
    await run(SyncWeekdaySlotTemplatesRequest(trainer_id=trainer.id, weekday=day.weekday(), time_capacities={T10: 1}))
    [slot] = await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))

    occurrence = await run(AddRecurringBookingRequest(trainer_id=trainer.id, client_id=client.id, slot_id=slot.id))
    await run(MaintainRecurringBookingsRequest())  # ещё не прошла — дубля нет
    assert len(await run(GetUpcomingBookingsByClientRequest(client_id=client.id))) == 1

    await run(DeactivateRecurringBookingRequest(recurring_booking_id=occurrence.recurring_booking_id))

    assert await run(GetUpcomingBookingsByClientRequest(client_id=client.id)) == []
    texts = [text for _, text in notifications.of("send")]
    assert any("отменил вашу тренировку" in t for t in texts)
    assert any("Постоянная запись остановлена" in t for t in texts)

    await run(MaintainRecurringBookingsRequest())
    assert await run(GetUpcomingBookingsByClientRequest(client_id=client.id)) == []


async def _recurring_slots(run, trainer, *days: int):
    """Слот на 10:00 в каждый из дней (смещение от сегодня)."""
    slots = []
    for offset in days:
        day = get_project_today() + timedelta(days=offset)
        await run(SyncWeekdaySlotTemplatesRequest(trainer_id=trainer.id, weekday=day.weekday(), time_capacities={T10: 1}))
        [slot] = await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))
        slots.append(slot)
    return slots


async def test_cancelled_recurring_occurrence_can_be_restored(run) -> None:
    trainer, client = await _trainer_and_client(run)
    [slot] = await _recurring_slots(run, trainer, 2)
    add = AddRecurringBookingRequest(trainer_id=trainer.id, client_id=client.id, slot_id=slot.id)
    occurrence = await run(add)
    await run(CancelBookingRequest(booking_id=occurrence.id))

    # раньше — «уже есть постоянная запись», и помогал только стоп + заново
    restored = await run(add)
    assert restored.recurring_booking_id == occurrence.recurring_booking_id
    assert restored.status == BookingStatus.CONFIRMED
    [upcoming] = await run(GetUpcomingBookingsByClientRequest(client_id=client.id))
    assert upcoming.id == restored.id

    # тренировка уже стоит — второй раз «вернуть» нечего
    with pytest.raises(RecurringBookingAlreadyExistsException):
        await run(add)


async def test_change_after_cancel_creates_training_on_new_day(run) -> None:
    trainer, client = await _trainer_and_client(run)
    old_slot, new_slot = await _recurring_slots(run, trainer, 2, 3)
    occurrence = await run(AddRecurringBookingRequest(trainer_id=trainer.id, client_id=client.id, slot_id=old_slot.id))
    await run(CancelBookingRequest(booking_id=occurrence.id))

    await run(ChangeRecurringBookingScheduleRequest(recurring_booking_id=occurrence.recurring_booking_id, new_slot_id=new_slot.id))

    [upcoming] = await run(GetUpcomingBookingsByClientRequest(client_id=client.id))
    assert upcoming.slot_id == new_slot.id
    assert upcoming.recurring_booking_id == occurrence.recurring_booking_id
    await run(MaintainRecurringBookingsRequest())  # ещё не прошла — дубля нет
    assert len(await run(GetUpcomingBookingsByClientRequest(client_id=client.id))) == 1


async def test_failed_recurring_add_leaves_no_template(run) -> None:
    trainer, client = await _trainer_and_client(run)
    [slot] = await _recurring_slots(run, trainer, 2)
    await run(SetSlotBlockedRequest(slot_id=slot.id, blocked=True))
    add = AddRecurringBookingRequest(trainer_id=trainer.id, client_id=client.id, slot_id=slot.id)

    with pytest.raises(SlotAlreadyBookedException):
        await run(add)
    assert await run(GetActiveRecurringBookingsByClientRequest(trainer_id=trainer.id, client_id=client.id)) == []

    # слот открыли — добавление проходит, без «уже есть постоянная запись»
    await run(SetSlotBlockedRequest(slot_id=slot.id, blocked=False))
    assert (await run(add)).status == BookingStatus.CONFIRMED


async def test_client_requests_flow(run, notifications) -> None:
    trainer, client = await _trainer_and_client(run)
    await run(
        CreateProgramRequestRequest(
            client_id=client.id, trainer_id=trainer.id, program_type=ProgramType.WEEK_3,
            direction=TrainingDirection.OFP, comment="<b>цель</b>",
        )
    )
    feedback = await run(CreateFeedbackRequest(client_id=client.id, trainer_id=trainer.id, message="Привет"))

    new = await run(GetClientRequestsByTrainerRequest(trainer_id=trainer.id))
    assert [r.kind for r in new] == [ClientRequestKind.FEEDBACK, ClientRequestKind.PROGRAM]
    assert len(notifications.of("notify_client_request")) == 2

    await run(UpdateClientRequestStatusRequest(kind=feedback.kind, request_id=feedback.id, status=RequestStatus.DONE))
    assert len(await run(GetClientRequestsByTrainerRequest(trainer_id=trainer.id))) == 1


async def test_subscription_grant_expiry_and_access(run, notifications, container) -> None:
    trainer, client = await _trainer_and_client(run)
    access = await run(GetUserAccessRequest(tg_id=client.tg_id))
    assert not access.client_trainer_available  # подписки ещё нет

    await run(GrantSubscriptionRequest(trainer_id=trainer.id, source=SubscriptionSource.TRIAL, days=1))
    assert (await run(GetUserAccessRequest(tg_id=client.tg_id))).client_trainer_available

    # подписка на 1 день → крон шлёт предупреждение (порог 48 ч) один раз
    await run(CheckExpiringSubscriptionsRequest())
    await run(CheckExpiringSubscriptionsRequest())
    events = [e.event.value for e in notifications.of("notify_subscription")]
    assert events == ["granted", "warning"]

    await run(SetTrainerBlockedRequest(trainer_id=trainer.id, blocked=True))
    assert (await run(GetUserAccessRequest(tg_id=trainer.tg_id))).is_blocked
    assert not (await run(GetUserAccessRequest(tg_id=client.tg_id))).client_trainer_available


async def test_admin_stats_reports_and_exports(run) -> None:
    trainer, client = await _trainer_and_client(run)
    other, _ = await _trainer_and_client(run, trainer_tg=1003, client_tg=2004)
    await run(GrantSubscriptionRequest(trainer_id=trainer.id, source=SubscriptionSource.CASH, days=30, amount=Decimal("50")))
    await run(GrantSubscriptionRequest(trainer_id=other.id, source=SubscriptionSource.TRIAL, days=7))
    await run(SetClientBlockedRequest(client_id=client.id, blocked=True))

    stats = await run(GetAdminOverviewStatsRequest(period=StatsPeriod.TODAY))
    assert (stats.trainers_total, stats.trainers_new, stats.trainers_with_subscription) == (2, 2, 2)
    assert (stats.clients_total, stats.clients_new, stats.clients_blocked) == (2, 2, 1)
    assert stats.revenue_period == Decimal("50") and stats.revenue_cash == Decimal("50")
    assert (stats.payments_count, stats.trials_count) == (1, 1)

    report = await run(GetAdminTrainerReportRequest(trainer_id=trainer.id, period=StatsPeriod.ALL))
    assert report.paid_total == Decimal("50") and report.clients_total == 1
    assert report.subscription is not None

    for kind in ReportKind:
        export = await run(ExportReportRequest(kind=kind))
        assert export.content.startswith("﻿".encode())  # BOM для Excel
        assert export.filename.endswith(".csv")
    trainers_csv = (await run(ExportReportRequest(kind=ReportKind.TRAINERS))).content.decode("utf-8-sig")
    assert "Тренер 1001" in trainers_csv and "50.00" in trainers_csv


async def test_faq_seed_for_both_audiences(run, container) -> None:
    await seed_faq_items(container)
    await seed_faq_items(container)  # повторный запуск не дублирует
    clients_faq = await run(GetActiveFaqItemsRequest(audience=FaqAudience.CLIENT))
    trainers_faq = await run(GetActiveFaqItemsRequest(audience=FaqAudience.TRAINER))
    assert len(clients_faq) == 9 and len(trainers_faq) == 21
    assert any("подписка" in item.question.lower() for item in trainers_faq)


async def test_export_on_empty_db(run) -> None:
    export = await run(ExportReportRequest(kind=ReportKind.BOOKINGS))
    assert export.rows == 0
