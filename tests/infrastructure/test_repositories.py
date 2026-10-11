from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from src.domain.entities.faq import FaqItem
from src.domain.entities.feedback import FeedbackMessage
from src.domain.enums.booking import BookingStatus
from src.domain.enums.faq import FaqAudience
from src.domain.enums.request import RequestStatus
from src.domain.utils import get_project_today
from src.infrastructure.repositories.booking.sqlalchemy import SQLAlchemyBookingRepo
from src.infrastructure.repositories.calendar_slot.sqlalchemy import SQLAlchemyCalendarSlotRepo
from src.infrastructure.repositories.client.sqlalchemy import SQLAlchemyClientRepo
from src.infrastructure.repositories.faq.sqlalchemy import SQLAlchemyFaqRepo
from src.infrastructure.repositories.feedback.sqlalchemy import SQLAlchemyFeedbackRepo
from src.infrastructure.repositories.subscription.sqlalchemy import (
    SQLAlchemyTrainerSubscriptionRepo,
)
from tests.factories import (
    make_booking,
    make_client,
    make_slot,
    make_subscription,
    make_trainer,
)


async def test_booking_price_and_job_ids_persisted(session) -> None:
    # регресс: модель не маппила price, а job id терялись без commit
    trainer = await make_trainer(session)
    client = await make_client(session, trainer.id)
    slot = await make_slot(session, trainer.id, get_project_today() + timedelta(days=1))
    booking = await make_booking(
        session, client, slot, BookingStatus.CONFIRMED,
        price=Decimal("25.50"), reminder_job_id="r1", completion_job_id="c1",
    )

    session.expunge_all()
    stored = await SQLAlchemyBookingRepo(session).get_by_id(booking.id)
    assert stored.price == Decimal("25.50")
    assert (stored.reminder_job_id, stored.completion_job_id) == ("r1", "c1")


async def test_count_by_trainer_and_status_uses_slot_date(session) -> None:
    trainer = await make_trainer(session)
    client = await make_client(session, trainer.id)
    today = get_project_today()
    in_range = await make_slot(session, trainer.id, today)
    out_of_range = await make_slot(session, trainer.id, today + timedelta(days=40))
    await make_booking(session, client, in_range, BookingStatus.COMPLETED)
    await make_booking(session, client, out_of_range, BookingStatus.COMPLETED)

    counts = await SQLAlchemyBookingRepo(session).count_by_trainer_and_status(today, today)
    assert counts == {(trainer.id, BookingStatus.COMPLETED): 1}


async def test_upcoming_by_recurring_ignores_past_and_inactive(session) -> None:
    from src.domain.entities.recurring_booking import RecurringBooking
    from src.infrastructure.repositories.recurring_booking.sqlalchemy import (
        SQLAlchemyRecurringBookingRepo,
    )

    trainer = await make_trainer(session)
    client = await make_client(session, trainer.id)
    recurring = await SQLAlchemyRecurringBookingRepo(session).save(
        RecurringBooking(trainer_id=trainer.id, client_id=client.id, weekday=0, start_time=time(10, 0, tzinfo=timezone.utc))
    )
    await session.commit()
    today = get_project_today()
    future = await make_slot(session, trainer.id, today + timedelta(days=3))
    past = await make_slot(session, trainer.id, today - timedelta(days=3))
    cancelled = await make_slot(session, trainer.id, today + timedelta(days=10))
    keep = await make_booking(session, client, future, BookingStatus.CONFIRMED, recurring_booking_id=recurring.id)
    await make_booking(session, client, past, BookingStatus.CONFIRMED, recurring_booking_id=recurring.id)
    await make_booking(session, client, cancelled, BookingStatus.CANCELLED, recurring_booking_id=recurring.id)

    result = await SQLAlchemyBookingRepo(session).get_upcoming_by_recurring_booking_id(recurring.id)
    assert [b.id for b in result] == [keep.id]


async def test_cancelled_stats_include_today(session) -> None:
    # регресс: updated_at сравнивался с голой датой и «сегодня» всегда давало 0
    trainer = await make_trainer(session)
    client = await make_client(session, trainer.id)
    slot = await make_slot(session, trainer.id, get_project_today())
    await make_booking(session, client, slot, BookingStatus.CANCELLED)

    today = get_project_today()
    count = await SQLAlchemyBookingRepo(session).count_cancelled_by_trainer_in_period(
        trainer.id, today, today
    )
    assert count == 1


async def test_client_search(session) -> None:
    trainer = await make_trainer(session)
    await make_client(session, trainer.id, tg_id=555, first_name="Анна", username="anna_fit", phone="+375291111111")
    await make_client(session, trainer.id, tg_id=556, first_name="Борис", phone="+375292222222")
    repo = SQLAlchemyClientRepo(session)

    assert [c.first_name for c in await repo.search("анн")] == ["Анна"]
    assert [c.first_name for c in await repo.search("@anna")] == ["Анна"]
    assert [c.first_name for c in await repo.search("2222")] == ["Борис"]
    assert [c.first_name for c in await repo.search("556")] == ["Борис"]
    assert len(await repo.search("")) == 2


async def test_active_subscription_is_the_longest(session) -> None:
    # регресс: при продлении активных подписок две, бралась произвольная
    trainer = await make_trainer(session)
    await make_subscription(session, trainer.id, timedelta(days=5))
    longest = await make_subscription(session, trainer.id, timedelta(days=35))
    await make_subscription(session, trainer.id, timedelta(days=-1))

    active = await SQLAlchemyTrainerSubscriptionRepo(session).get_active_by_trainer_id(trainer.id)
    assert active.id == longest.id


async def test_faq_filtered_by_audience_and_ordered(session) -> None:
    repo = SQLAlchemyFaqRepo(session)
    await repo.save(FaqItem(question="T2", answer="a", order=2, audience=FaqAudience.TRAINER))
    await repo.save(FaqItem(question="T1", answer="a", order=1, audience=FaqAudience.TRAINER))
    await repo.save(FaqItem(question="C", answer="a", audience=FaqAudience.CLIENT))
    await repo.save(FaqItem(question="off", answer="a", is_active=False, audience=FaqAudience.TRAINER))
    await session.commit()

    assert [f.question for f in await repo.get_active(FaqAudience.TRAINER)] == ["T1", "T2"]
    assert [f.question for f in await repo.get_active(FaqAudience.CLIENT)] == ["C"]


async def test_feedback_by_trainer_and_status_counts(session) -> None:
    trainer = await make_trainer(session)
    other = await make_trainer(session, tg_id=101)
    client = await make_client(session, trainer.id)
    repo = SQLAlchemyFeedbackRepo(session)
    await repo.save(FeedbackMessage(client_id=client.id, trainer_id=trainer.id, phone="+1", message=None))
    await repo.save(FeedbackMessage(client_id=client.id, trainer_id=trainer.id, phone=None, message="hi", status=RequestStatus.DONE))
    await repo.save(FeedbackMessage(client_id=client.id, trainer_id=other.id, phone="+2", message=None))
    await session.commit()

    new = await repo.get_by_trainer_id(trainer.id, [RequestStatus.NEW])
    assert len(new) == 1 and new[0].is_callback_request()

    now = datetime.now(timezone.utc)
    counts = await repo.count_by_trainer_created_between(now - timedelta(hours=1), now + timedelta(hours=1))
    assert counts == {trainer.id: 2, other.id: 1}


async def test_slots_by_ids(session) -> None:
    trainer = await make_trainer(session)
    a = await make_slot(session, trainer.id, get_project_today())
    await make_slot(session, trainer.id, get_project_today(), start=time(12, 0))
    repo = SQLAlchemyCalendarSlotRepo(session)
    assert [s.id for s in await repo.get_by_ids([a.id])] == [a.id]
    assert await repo.get_by_ids([]) == []
