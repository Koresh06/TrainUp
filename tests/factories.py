"""Создание данных в реальной БД через репозитории (для integration-тестов)."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.booking import BookingStatus
from src.domain.enums.subscription import (
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
)
from src.domain.enums.training import SportExperience
from src.infrastructure.repositories.booking.sqlalchemy import SQLAlchemyBookingRepo
from src.infrastructure.repositories.calendar_slot.sqlalchemy import SQLAlchemyCalendarSlotRepo
from src.infrastructure.repositories.client.sqlalchemy import SQLAlchemyClientRepo
from src.infrastructure.repositories.subscription.sqlalchemy import (
    SQLAlchemyTrainerSubscriptionRepo,
)
from src.infrastructure.repositories.trainer.sqlalchemy import SQLAlchemyTrainerRepo


async def make_trainer(session: AsyncSession, tg_id: int = 100, **kwargs) -> Trainer:
    trainer = await SQLAlchemyTrainerRepo(session).save(
        Trainer(
            tg_id=tg_id,
            name=kwargs.pop("name", f"Тренер {tg_id}"),
            bio="",
            notification_chat_id=-tg_id,
            is_active=kwargs.pop("is_active", True),
            **kwargs,
        )
    )
    await session.commit()
    return trainer


async def make_client(session: AsyncSession, trainer_id: int, tg_id: int = 1000, **kwargs) -> Client:
    client = await SQLAlchemyClientRepo(session).save(
        Client(
            tg_id=tg_id,
            trainer_id=trainer_id,
            first_name=kwargs.pop("first_name", "Пётр"),
            last_name=kwargs.pop("last_name", None),
            username=kwargs.pop("username", None),
            phone=kwargs.pop("phone", "+375291234567"),
            age=30,
            sport_experience=SportExperience.NONE,
            **kwargs,
        )
    )
    await session.commit()
    return client


async def make_slot(
    session: AsyncSession, trainer_id: int, slot_date: date, start: time = time(10, 0), **kwargs
) -> CalendarSlot:
    slot = await SQLAlchemyCalendarSlotRepo(session).save(
        CalendarSlot(
            trainer_id=trainer_id,
            slot_date=slot_date,
            start_time=start.replace(tzinfo=timezone.utc),
            end_time=time(start.hour + 1, start.minute, tzinfo=timezone.utc),
            **kwargs,
        )
    )
    await session.commit()
    return slot


async def make_booking(
    session: AsyncSession, client: Client, slot: CalendarSlot, status: BookingStatus, **kwargs
) -> Booking:
    booking = await SQLAlchemyBookingRepo(session).save(
        Booking(client_id=client.id, trainer_id=slot.trainer_id, slot_id=slot.id, status=status, **kwargs)
    )
    await session.commit()
    return booking


async def make_subscription(
    session: AsyncSession,
    trainer_id: int,
    expires_in: timedelta = timedelta(days=30),
    source: SubscriptionSource = SubscriptionSource.PURCHASE,
    amount: Decimal = Decimal("30"),
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
) -> TrainerSubscription:
    now = datetime.now(timezone.utc)
    subscription = await SQLAlchemyTrainerSubscriptionRepo(session).save(
        TrainerSubscription(
            trainer_id=trainer_id,
            plan=SubscriptionPlan.ONE_MONTH,
            amount=amount,
            status=status,
            started_at=now,
            expired_at=now + expires_in,
            source=source,
        )
    )
    await session.commit()
    return subscription
