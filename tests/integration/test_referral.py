"""Реферальная программа: приглашение, привязка, бонус за первую тренировку друга."""

from datetime import time, timedelta, timezone

from src.application.use_cases.booking.create_by_trainer import CreateBookingByTrainerRequest
from src.application.use_cases.booking.mark_completed import MarkBookingCompletedRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.client.referral import (
    GetReferralInfoRequest,
    ResolveReferralCodeRequest,
)
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.package.get_by_client import GetClientPackagesRequest
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer_booking_settings.update import (
    UpdateTrainerBookingSettingsRequest,
)
from src.domain.utils import get_project_today

T10 = time(10, 0, tzinfo=timezone.utc)
T12 = time(12, 0, tzinfo=timezone.utc)


def register(trainer_id: int, tg_id: int, name: str, referred_by: int | None = None):
    return RegisterClientRequest(
        tg_id=tg_id, trainer_id=trainer_id, first_name=name, last_name=None, username=None,
        phone="+375291234567", age=30, sport_experience="none", answers={},
        referred_by_client_id=referred_by,
    )


async def test_referral_bonus_once(run, notifications) -> None:
    trainer = await run(RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1))
    other = await run(RegisterTrainerRequest(tg_id=1002, name="Чужой", bio="", notification_chat_id=-2))
    await run(
        UpdateTrainerBookingSettingsRequest(
            trainer_id=trainer.id, calendar_horizon_days=14, max_active_bookings_per_client=1,
            referral_bonus_sessions=2,
        )
    )
    petr = await run(register(trainer.id, 2001, "Пётр"))
    info = await run(GetReferralInfoRequest(client_id=petr.id))
    assert info.code and info.bonus_sessions == 2 and info.invited == []
    assert (await run(ResolveReferralCodeRequest(code=info.code))).id == petr.id

    anna = await run(register(trainer.id, 2002, "Анна", referred_by=petr.id))
    assert anna.referred_by_client_id == petr.id
    texts = [t for _, t in notifications.of("send")]
    assert any("пришёл по приглашению" in t for t in texts)
    assert any("Ваш друг <b>Анна</b> присоединился" in t for t in texts)

    # приглашение к чужому тренеру не засчитывается
    stranger = await run(register(other.id, 2003, "Олег", referred_by=petr.id))
    assert stranger.referred_by_client_id is None

    day = get_project_today() + timedelta(days=1)
    await run(SyncWeekdaySlotTemplatesRequest(trainer_id=trainer.id, weekday=day.weekday(), time_capacities={T10: 1, T12: 1}))
    slots = sorted(await run(GetDaySlotsRequest(trainer_id=trainer.id, slot_date=day)), key=lambda s: s.start_time)
    for slot in slots:
        booking = await run(CreateBookingByTrainerRequest(trainer_id=trainer.id, client_id=anna.id, slot_id=slot.id))
        await run(MarkBookingCompletedRequest(booking_id=booking.id))

    [bonus] = await run(GetClientPackagesRequest(client_id=petr.id))
    assert bonus.is_bonus and bonus.sessions_total == 2 and bonus.is_paid
    assert any("начислено бесплатных занятий: <b>2</b>" in t for c, t in notifications.of("send") if c == petr.tg_id)

    info = await run(GetReferralInfoRequest(client_id=petr.id))
    assert [c.id for c in info.invited] == [anna.id] and info.rewarded == 1
