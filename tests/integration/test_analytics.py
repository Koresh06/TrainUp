"""Аналитика: пользователи бота (новые/активные/заблокировавшие), статистика
тренера и ряды для графиков — на реальной БД."""

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from src.application.use_cases.admin.get_analytics import GetAdminAnalyticsRequest
from src.application.use_cases.bot_user.set_bot_blocked import SetBotBlockedByUserRequest
from src.application.use_cases.bot_user.track_activity import TrackUserActivityRequest
from src.application.use_cases.stats.get_trainer import GetTrainerStatsRequest
from src.application.use_cases.stats.period import StatsPeriod
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.domain.enums.booking import BookingStatus
from src.domain.enums.subscription import SubscriptionSource
from src.domain.utils import get_project_today
from src.infrastructure.repositories.bot_user.sqlalchemy import SQLAlchemyBotUserRepo
from tests.factories import make_booking, make_client, make_slot, make_trainer


async def test_bot_user_upsert_activity_and_block(session) -> None:
    repo = SQLAlchemyBotUserRepo(session)
    today = get_project_today()
    now = datetime.now(timezone.utc)

    # повторная отметка в тот же день — один пользователь и один день активности
    for name in ("Old", "New"):
        await repo.touch_activity(tg_id=1, username="u", first_name=name, now=now, activity_date=today)
    await repo.touch_activity(
        tg_id=1, username="u", first_name="New", now=now, activity_date=today - timedelta(days=1)
    )
    await session.commit()

    user = await repo.get_by_tg_id(1)
    assert user.first_name == "New" and not user.is_bot_blocked
    assert await repo.count_active(today, today) == 1
    assert await repo.count_active_by_bucket(today - timedelta(days=1), today, by_month=False) == {
        today - timedelta(days=1): 1, today: 1,
    }
    assert await repo.count_active_by_bucket(today, today, by_month=True) == {today.replace(day=1): 1}

    # блокирует тот, кого ещё нет в таблице (писал до запуска аналитики)
    await repo.set_bot_blocked(tg_id=2, blocked_at=now)
    await repo.set_bot_blocked(tg_id=1, blocked_at=now)
    await session.commit()
    assert (await repo.get_by_tg_id(2)).is_bot_blocked

    # написал боту снова — значит разблокировал
    await repo.touch_activity(tg_id=1, username="u", first_name="New", now=now, activity_date=today)
    await session.commit()
    session.expunge_all()
    assert not (await repo.get_by_tg_id(1)).is_bot_blocked


async def test_admin_analytics_users_funnel_and_series(session, run) -> None:
    trainer = await make_trainer(session, tg_id=10)
    paid_trainer = await make_trainer(session, tg_id=11)
    client = await make_client(session, trainer.id, tg_id=20)
    for tg_id in (10, 11, 20, 30, 31):  # 30, 31 — нажали /start и не зарегистрировались
        await run(TrackUserActivityRequest(tg_id=tg_id, first_name="X"))
    await run(SetBotBlockedByUserRequest(tg_id=31, blocked=True))
    await run(SetBotBlockedByUserRequest(tg_id=20, blocked=True))

    await run(GrantSubscriptionRequest(trainer_id=trainer.id, source=SubscriptionSource.TRIAL, days=7))
    await run(GrantSubscriptionRequest(trainer_id=paid_trainer.id, source=SubscriptionSource.TRIAL, days=7))
    await run(
        GrantSubscriptionRequest(
            trainer_id=paid_trainer.id, source=SubscriptionSource.CASH, days=30, amount=Decimal("30")
        )
    )
    today = get_project_today()
    slot = await make_slot(session, trainer.id, today)
    await make_booking(session, client, slot, BookingStatus.COMPLETED, price=Decimal("20"))

    a = await run(GetAdminAnalyticsRequest(period=StatsPeriod.WEEK))

    assert (a.users_total, a.trainers_total, a.clients_total, a.guests_total) == (5, 2, 1, 2)
    assert (a.users_new, a.guests_new) == (5, 2)
    assert (a.dau, a.wau, a.mau, a.active_period) == (5, 5, 5, 5)
    assert (a.blocked_total, a.blocked_new, a.blocked_clients, a.blocked_trainers) == (2, 2, 1, 0)
    assert (a.trainers_trial, a.trainers_paid, a.trainers_trial_to_paid) == (2, 1, 1)
    assert a.trainers_on_trial_now == 1

    s = a.series
    assert len(s.buckets) == 7 and not s.range.by_month
    i = s.buckets.index(today)
    assert (s.new_trainers[i], s.new_clients[i], s.new_guests[i]) == (2, 1, 2)
    assert s.active_users[i] == 5 and s.blocked_bot[i] == 2
    assert sum(s.revenue) == Decimal("30")  # пробные периоды — не выручка
    assert s.trainings_completed[i] == 1

    all_time = await run(GetAdminAnalyticsRequest(period=StatsPeriod.ALL))
    assert all_time.series.range.by_month and len(all_time.series.buckets) >= 6
    assert sum(all_time.series.active_users) == 5


async def test_trainer_stats_income_load_and_series(session, run) -> None:
    trainer = await make_trainer(session, tg_id=10)
    anna = await make_client(session, trainer.id, tg_id=20, first_name="Анна")
    boris = await make_client(session, trainer.id, tg_id=21, first_name="Борис", phone="+375292222222")
    today = get_project_today()
    yesterday = today - timedelta(days=1)

    for start, client, price in (
        (time(9), anna, Decimal("20")),
        (time(10), anna, Decimal("30")),
        (time(18), boris, None),  # цена не настроена — в средний чек не идёт
    ):
        slot = await make_slot(session, trainer.id, today, start=start)
        await make_booking(session, client, slot, BookingStatus.COMPLETED, price=price)
    future = await make_slot(session, trainer.id, today + timedelta(days=60), start=time(12))
    await make_booking(session, anna, future, BookingStatus.CONFIRMED, price=Decimal("40"))
    cancelled = await make_slot(session, trainer.id, yesterday, start=time(11))
    await make_booking(session, boris, cancelled, BookingStatus.CANCELLED)

    s = await run(GetTrainerStatsRequest(trainer_id=trainer.id, period=StatsPeriod.TODAY))

    assert (s.total_clients, s.new_clients, s.active_clients) == (2, 2, 2)
    assert s.completed_trainings == 3 and s.upcoming_bookings == 1
    assert s.income == Decimal("50") and s.average_check == Decimal("25")
    assert s.top_clients[0].name == "Анна" and s.top_clients[0].completed == 2
    assert s.cancel_rate == 0  # отмена вчерашняя — в «Сегодня» не входит

    # «Сегодня» на графике — последние 14 дней, вчерашняя отмена там видна
    series = s.series
    assert len(series.buckets) == 14 and series.buckets[-1] == today
    assert series.completed[-1] == 3 and series.income[-1] == Decimal("50")
    assert series.cancelled[-2] == 1
    assert series.load[today.weekday()][9] == 1 and series.load[today.weekday()][18] == 1
    assert sum(map(sum, series.load)) == 3  # отменённые не грузят расписание

    all_time = await run(GetTrainerStatsRequest(trainer_id=trainer.id, period=StatsPeriod.ALL))
    assert all_time.cancel_rate == 1 / 4
    assert all_time.series.range.by_month
