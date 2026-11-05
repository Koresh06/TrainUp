"""Архив клиентов тренера: клиент ушёл, но остаётся в статистике."""

from datetime import time, timedelta, timezone

import pytest

from src.application.use_cases.booking.create_by_trainer import (
    CreateBookingByTrainerRequest,
)
from src.application.use_cases.booking.get_views import GetBookingViewsRequest
from src.application.use_cases.access.get_user_access import GetUserAccessRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.client.archive import (
    ArchiveClientRequest,
    RestoreClientRequest,
)
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.mailing.execute import ExecuteMailingRequest
from src.application.use_cases.recurring_booking.add import AddRecurringBookingRequest
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerRequest,
)
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesRequest,
)
from src.application.use_cases.stats.get_trainer import GetTrainerStatsRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.domain.enums.booking import BookingActor, BookingStatus
from src.domain.enums.mailing import MailingTarget
from src.domain.exception.client import ClientAccessDeniedException
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
    client = await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=trainer.id, first_name="Пётр", last_name=None,
            username=None, phone="+375291234567", age=30, sport_experience="none", answers={},
        )
    )
    return {"trainer": trainer, "client": client, "s10": slots[T10], "s12": slots[T12]}


async def test_archive_cancels_silently_and_keeps_history(run, world, notifications) -> None:
    trainer, client = world["trainer"], world["client"]
    await run(
        AddRecurringBookingRequest(trainer_id=trainer.id, client_id=client.id, slot_id=world["s10"].id)
    )
    await run(
        CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=client.id, slot_id=world["s12"].id)
    )
    notifications.calls.clear()

    result = await run(ArchiveClientRequest(trainer_id=trainer.id, client_id=client.id))
    assert result.client.is_archived
    assert result.cancelled_bookings == 2 and result.stopped_recurring == 1

    # одно сообщение клиенту вместо сообщения на каждую отмену
    assert [chat for chat, _ in notifications.of("send")] == [client.tg_id]
    assert await run(GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer.id)) == []

    views = await run(GetBookingViewsRequest(trainer_id=trainer.id, client_id=client.id))
    assert {v.booking.status for v in views} == {BookingStatus.CANCELLED}
    assert {v.booking.cancelled_by for v in views} == {BookingActor.TRAINER}
    # слоты освободились
    assert all(s.is_available() for s in await run(
        GetDaySlotsRequest(trainer_id=trainer.id, slot_date=world["s10"].slot_date)
    ))

    # в списках тренера его нет, в архиве и статистике — есть
    assert await run(GetClientsByTrainerIdRequest(trainer_id=trainer.id)) == []
    [archived] = await run(GetClientsByTrainerIdRequest(trainer_id=trainer.id, archived=True))
    assert archived.id == client.id
    stats = await run(GetTrainerStatsRequest(trainer_id=trainer.id))
    assert stats.total_clients == 1

    # записываться к тренеру он не может, а рассылка «клиентам тренера» его пропускает
    access = await run(GetUserAccessRequest(tg_id=client.tg_id))
    assert not access.client_trainer_available
    total = await run(
        ExecuteMailingRequest(
            target=MailingTarget.TRAINER_CLIENTS, from_chat_id=1, message_id=1,
            trainer_id=trainer.id,
        )
    )
    assert total == 0


async def test_restore_and_foreign_trainer(run, world, notifications) -> None:
    trainer, client = world["trainer"], world["client"]
    other = await run(RegisterTrainerRequest(tg_id=1002, name="Чужой", bio="", notification_chat_id=-2))
    with pytest.raises(ClientAccessDeniedException):
        await run(ArchiveClientRequest(trainer_id=other.id, client_id=client.id))

    await run(ArchiveClientRequest(trainer_id=trainer.id, client_id=client.id))
    notifications.calls.clear()
    restored = await run(
        RestoreClientRequest(trainer_id=trainer.id, client_id=client.id, by_client=True)
    )
    assert not restored.is_archived
    # тренер узнаёт, что клиент вернулся сам
    assert [chat for chat, _ in notifications.of("send")] == [trainer.notification_chat_id]

    # повторная архивация/возврат — без ошибок и без лишних сообщений
    await run(RestoreClientRequest(trainer_id=trainer.id, client_id=client.id))
    assert len(notifications.of("send")) == 1


async def test_offline_client_archive_sends_nothing(run, world, notifications) -> None:
    offline = await run(CreateOfflineClientRequest(trainer_id=world["trainer"].id, first_name="Олег"))
    notifications.calls.clear()
    await run(ArchiveClientRequest(trainer_id=world["trainer"].id, client_id=offline.id))
    assert notifications.of("send") == []
