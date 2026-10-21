"""Отпуск тренера: закрытие периода, отмена записей, будущие слоты, постоянные."""

from datetime import time, timedelta, timezone

import pytest

from src.application.use_cases.booking.create_by_trainer import CreateBookingByTrainerRequest
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.calendar.maintain_calendar_buffer import (
    MaintainCalendarBufferRequest,
)
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.vacation.create import CreateVacationRequest
from src.application.use_cases.vacation.manage import DeleteVacationRequest, GetVacationsRequest
from src.application.use_cases.vacation.preview import PreviewVacationRequest
from src.domain.enums.booking import BookingActor, BookingStatus
from src.domain.enums.slot import SlotStatus
from src.domain.exception.vacation import InvalidVacationPeriodException
from src.domain.utils import get_project_today

T10 = time(10, 0, tzinfo=timezone.utc)


async def test_vacation_flow(run, notifications) -> None:
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    day = get_project_today() + timedelta(days=1)
    for d in range(7):
        await run(
            SyncWeekdaySlotTemplatesRequest(trainer_id=trainer.id, weekday=d, time_capacities={T10: 2})
        )
    [slot] = await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))
    petr = await run(
        RegisterClientRequest(
            tg_id=2002, trainer_id=trainer.id, first_name="Пётр", last_name=None, username=None,
            phone="+375291234567", age=30, sport_experience="none", answers={},
        )
    )
    oleg = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Олег"))
    b1 = await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=petr.id, slot_id=slot.id))
    await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=oleg.id, slot_id=slot.id))

    preview = await run(PreviewVacationRequest(trainer_id=trainer.id, date_from=day, date_to=day + timedelta(days=2)))
    assert preview.slots_to_block == 3 and len(preview.bookings) == 2
    assert preview.offline_clients == ["Олег"]

    with pytest.raises(InvalidVacationPeriodException):
        await run(CreateVacationRequest(trainer_id=trainer.id, date_from=day, date_to=day - timedelta(days=1)))

    notifications.calls.clear()
    far_end = get_project_today() + timedelta(days=80)  # за пределами уже созданных слотов
    await run(CreateVacationRequest(trainer_id=trainer.id, date_from=day, date_to=far_end))

    cancelled = await run(GetBookingByIdRequest(booking_id=b1.id))
    assert cancelled.status == BookingStatus.CANCELLED and cancelled.cancelled_by == BookingActor.TRAINER
    [(chat_id, text)] = notifications.of("send")
    assert chat_id == petr.tg_id and "тренер не проводит тренировки" in text
    assert all(
        s.status == SlotStatus.BLOCKED
        for s in await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))
    )

    # календарь догенерирует слоты внутри отпуска — они сразу закрыты
    await run(MaintainCalendarBufferRequest())
    late_day = get_project_today() + timedelta(days=60)
    late_slots = await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=late_day))
    assert late_slots and all(s.status == SlotStatus.BLOCKED for s in late_slots)

    [vacation] = await run(GetVacationsRequest(trainer_id=trainer.id))
    opened = await run(DeleteVacationRequest(trainer_id=trainer.id, vacation_id=vacation.id))
    assert opened > 0
    assert all(
        s.status == SlotStatus.FREE
        for s in await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day))
    )
