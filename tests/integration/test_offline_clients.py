"""Клиенты без Telegram и запись клиента тренером: use case'ы на реальной БД."""

from datetime import time, timedelta, timezone

import pytest

from src.application.use_cases.booking.cancel import CancelBookingRequest
from src.application.use_cases.booking.create_by_trainer import (
    CreateBookingByTrainerRequest,
)
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.booking.get_views import GetBookingViewsRequest
from src.application.use_cases.booking.reschedule import RescheduleBookingRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.client.claim_invite import ClaimClientInviteRequest
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.client.delete_offline import DeleteOfflineClientRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.client.update_by_trainer import UpdateClientFieldRequest
from src.application.use_cases.mailing.execute import ExecuteMailingRequest
from src.application.use_cases.recurring_booking.add import AddRecurringBookingRequest
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesRequest,
)
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.domain.enums.booking import BookingStatus
from src.domain.enums.client import ClientEditableField, ClientSource
from src.domain.enums.mailing import MailingTarget
from src.domain.exception.booking import ClientAlreadyBookedThisSlotException
from src.domain.exception.calendar_slot import SlotFullException
from src.domain.exception.client import (
    ClientAccessDeniedException,
    ClientAlreadyExistsException,
    ClientHasBookingsException,
    ClientInviteNotFoundException,
)
from src.domain.utils import get_project_today

T10 = time(10, 0, tzinfo=timezone.utc)
T12 = time(12, 0, tzinfo=timezone.utc)


@pytest.fixture
async def world(run):
    trainer = await run(
        RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1)
    )
    day = get_project_today() + timedelta(days=1)
    await run(
        SyncWeekdaySlotTemplatesRequest(
            trainer_id=trainer.id, weekday=day.weekday(), time_capacities={T10: 1, T12: 1}
        )
    )
    slots = {s.start_time: s for s in await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))}
    offline = await run(
        CreateOfflineClientRequest(trainer_id=trainer.id, first_name="  Олег ", last_name="Ким")
    )
    return {"trainer": trainer, "offline": offline, "s10": slots[T10], "s12": slots[T12]}


async def test_offline_client_card(run, world) -> None:
    client = world["offline"]
    assert client.tg_id is None and client.source == ClientSource.MANUAL
    assert client.first_name == "Олег" and client.invite_token

    updated = await run(
        UpdateClientFieldRequest(
            trainer_id=world["trainer"].id, client_id=client.id,
            field=ClientEditableField.TRAINER_NOTE, value="колено",
        )
    )
    assert updated.trainer_note == "колено"

    other = await run(RegisterTrainerRequest(tg_id=1002, name="Чужой", bio="", notification_chat_id=-2))
    with pytest.raises(ClientAccessDeniedException):
        await run(
            UpdateClientFieldRequest(
                trainer_id=other.id, client_id=client.id,
                field=ClientEditableField.PHONE, value="+70000000000",
            )
        )


async def test_trainer_books_offline_client_without_notifications(
    run, world, notifications, task_queue
) -> None:
    trainer, client, s10, s12 = world["trainer"], world["offline"], world["s10"], world["s12"]

    booking = await run(
        CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=s10.id)
    )
    assert booking.status == BookingStatus.CONFIRMED
    with pytest.raises(ClientAlreadyBookedThisSlotException):
        await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=s10.id))

    # напоминание клиенту не ставится, автозавершение — ставится
    scheduled = [name for name, *_ in task_queue.scheduled]
    assert scheduled == ["mark_booking_completed"]

    # вместимость слота уважается и для записи тренером
    second = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Анна"))
    with pytest.raises(SlotFullException):
        await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=second.id, slot_id=s10.id))

    await run(RescheduleBookingRequest(booking_id=booking.id, new_slot_id=s12.id))
    await run(CancelBookingRequest(booking_id=booking.id))
    assert notifications.of("send") == []
    assert notifications.of("notify_new_booking") == []

    [view] = await run(GetBookingViewsRequest(trainer_id=trainer.id, client_id=client.id))
    assert view.booking.status == BookingStatus.CANCELLED
    assert view.client_full_name == "Олег Ким" and not view.client_has_telegram


async def test_recurring_for_offline_client_is_silent(run, world, notifications, task_queue) -> None:
    occurrence = await run(
        AddRecurringBookingRequest(
            trainer_id=world["trainer"].id, client_id=world["offline"].id, slot_id=world["s10"].id
        )
    )
    assert occurrence.status == BookingStatus.CONFIRMED
    assert notifications.of("send") == []
    assert "send_training_reminder" not in [name for name, *_ in task_queue.scheduled]


async def test_mailing_skips_offline_clients(run, world, task_queue) -> None:
    await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=world["trainer"].id, first_name="Пётр", last_name=None,
            username=None, phone="+375291234567", age=30, sport_experience="none", answers={},
        )
    )
    total = await run(
        ExecuteMailingRequest(
            target=MailingTarget.TRAINER_CLIENTS, from_chat_id=1, message_id=1,
            trainer_id=world["trainer"].id,
        )
    )
    assert total == 1


async def test_claim_personal_link(run, world, notifications) -> None:
    client = world["offline"]
    booking = await run(
        CreateBookingByTrainerRequest(
            trainer_id=world["trainer"].id, client_id=client.id, slot_id=world["s10"].id
        )
    )

    claimed = await run(ClaimClientInviteRequest(token=client.invite_token, tg_id=3003, username="oleg"))
    assert claimed.id == client.id and claimed.tg_id == 3003 and claimed.invite_token is None
    assert any("подключился к боту" in text for _, text in notifications.of("send"))

    # ссылка одноразовая, а история сохраняется
    with pytest.raises(ClientInviteNotFoundException):
        await run(ClaimClientInviteRequest(token=client.invite_token, tg_id=3004, username=None))
    stored = await run(GetBookingByIdRequest(booking_id=booking.id))
    assert stored.client_id == client.id

    # у этого Telegram уже есть профиль — карточку не перепривязываем
    other = await run(CreateOfflineClientRequest(trainer_id=world["trainer"].id, first_name="Анна"))
    with pytest.raises(ClientAlreadyExistsException):
        await run(ClaimClientInviteRequest(token=other.invite_token, tg_id=3003, username=None))


async def test_delete_only_without_history(run, world) -> None:
    trainer = world["trainer"]
    mistake = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Ошибка"))
    await run(DeleteOfflineClientRequest(trainer_id=trainer.id, client_id=mistake.id))
    with pytest.raises(Exception):
        await run(GetClientByIdRequest(client_id=mistake.id))

    await run(
        CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=world["offline"].id, slot_id=world["s10"].id)
    )
    with pytest.raises(ClientHasBookingsException):
        await run(DeleteOfflineClientRequest(trainer_id=trainer.id, client_id=world["offline"].id))


async def test_no_show_and_cancelled_by(run, world, session, task_queue) -> None:
    from src.application.use_cases.booking.mark_attendance import MarkBookingAttendanceRequest
    from src.application.use_cases.stats.get_trainer import GetTrainerStatsRequest
    from src.application.use_cases.stats.period import StatsPeriod
    from src.domain.enums.booking import BookingActor
    from src.domain.exception.booking import (
        BookingStatusTransitionException,
        TrainingNotStartedException,
    )
    from tests.factories import make_booking, make_slot

    trainer, client = world["trainer"], world["offline"]

    future = await run(
        CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=world["s10"].id)
    )
    with pytest.raises(TrainingNotStartedException):
        await run(MarkBookingAttendanceRequest(trainer_id=trainer.id, booking_id=future.id, attended=False))

    await run(CancelBookingRequest(booking_id=future.id))
    cancelled = await run(GetBookingByIdRequest(booking_id=future.id))
    assert cancelled.cancelled_by == BookingActor.TRAINER and cancelled.cancelled_at is not None

    # тренировка сегодня рано утром уже прошла — автозавершение отметило «проведена»
    past_slot = await make_slot(session, trainer.id, get_project_today(), time(0, 0))
    past = await make_booking(session, client, past_slot, BookingStatus.COMPLETED)

    done = await run(MarkBookingAttendanceRequest(trainer_id=trainer.id, booking_id=past.id, attended=False))
    assert done.status == BookingStatus.NO_SHOW
    stats = await run(GetTrainerStatsRequest(trainer_id=trainer.id, period=StatsPeriod.TODAY))
    assert stats.no_show_trainings == 1 and stats.completed_trainings == 0

    back = await run(MarkBookingAttendanceRequest(trainer_id=trainer.id, booking_id=past.id, attended=True))
    assert back.status == BookingStatus.COMPLETED
    with pytest.raises(BookingStatusTransitionException):
        await run(MarkBookingAttendanceRequest(trainer_id=trainer.id, booking_id=past.id, attended=True))
