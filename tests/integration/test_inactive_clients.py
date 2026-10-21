"""«😴 Давно не были» и «📣 Позвать на тренировку»."""

from datetime import time, timedelta

import pytest

from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.client.get_inactive import GetInactiveClientsRequest
from src.application.use_cases.client.invite_back import InviteClientBackRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.domain.enums.booking import BookingStatus
from src.domain.exception.client import ClientAccessDeniedException
from src.domain.utils import get_project_today
from tests.factories import make_booking, make_slot


async def test_inactive_clients_and_invite_back(run, session, notifications) -> None:
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    today = get_project_today()

    async def client(tg_id, name):
        return await run(
            RegisterClientRequest(
                tg_id=tg_id, trainer_id=trainer.id, first_name=name, last_name=None, username=None,
                phone="+375291234567", age=30, sport_experience="none", answers={},
            )
        )

    lost = await client(2001, "Пропал")
    recent = await client(2002, "Недавно")
    booked = await client(2003, "Записан")
    offline = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Офлайн"))

    old_slot = await make_slot(session, trainer.id, today - timedelta(days=40), time(10, 0))
    old_slot2 = await make_slot(session, trainer.id, today - timedelta(days=30), time(10, 0))
    fresh_slot = await make_slot(session, trainer.id, today - timedelta(days=3), time(10, 0))
    future_slot = await make_slot(session, trainer.id, today + timedelta(days=2), time(10, 0))
    await make_booking(session, lost, old_slot, BookingStatus.COMPLETED)
    await make_booking(session, offline, old_slot2, BookingStatus.COMPLETED)
    await make_booking(session, recent, fresh_slot, BookingStatus.COMPLETED)
    await make_booking(session, booked, old_slot2, BookingStatus.COMPLETED)
    await make_booking(session, booked, future_slot, BookingStatus.CONFIRMED)

    inactive = await run(GetInactiveClientsRequest(trainer_id=trainer.id))
    assert [(d.client.first_name, d.days_since) for d in inactive] == [("Пропал", 40), ("Офлайн", 30)]

    await run(InviteClientBackRequest(trainer_id=trainer.id, client_id=lost.id))
    [message] = notifications.of("notify_plan_next_training")
    assert message.chat_id == lost.tg_id and message.days_since_training == 40

    with pytest.raises(ClientAccessDeniedException):
        await run(InviteClientBackRequest(trainer_id=trainer.id, client_id=offline.id))
