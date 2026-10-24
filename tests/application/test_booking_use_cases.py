from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

import pytest

from src.application.use_cases.booking.create import (
    CreateBookingRequest,
    CreateBookingUseCase,
)
from src.application.use_cases.booking.send_plan_next_reminder import (
    SendPlanNextTrainingReminderRequest,
    SendPlanNextTrainingReminderUseCase,
)
from src.application.use_cases.recurring_booking.maintain import (
    MaintainRecurringBookingsRequest,
    MaintainRecurringBookingsUseCase,
)
from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.booking import BookingStatus
from src.domain.enums.slot import SlotStatus
from src.domain.enums.subscription import (
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
)
from src.domain.enums.training import SportExperience
from src.domain.exception.booking import (
    ActiveBookingsLimitExceededException,
)
from src.domain.services.calendar_service import CalendarService
from src.domain.utils import get_project_today
from tests.fakes.booking import (
    FakeBookingRepository,
    FakeBookingScheduler,
    FakeClientRepository,
    FakeNoneRepository,
    FakeNotificationService,
    FakeRecurringBookingRepository,
    FakeTrainerRepository,
    FakeTransactionManager,
)
from tests.fakes.calendar import FakeCalendarSlotRepository, FakeSlotTemplateRepository
from tests.fakes.common import FakeSubscriptions

TRAINER = Trainer(
    id=1, tg_id=100, name="Тренер", bio="", notification_chat_id=-500, is_active=True
)
CLIENT = Client(
    id=7,
    tg_id=700,
    trainer_id=1,
    first_name="Иван",
    phone="+375291234567",
    age=30,
    sport_experience=SportExperience.NONE,
)
START = time(10, 0, tzinfo=timezone.utc)


def active_subscription(trainer_id: int = 1) -> TrainerSubscription:
    now = datetime.now(timezone.utc)
    return TrainerSubscription(
        trainer_id=trainer_id,
        plan=SubscriptionPlan.CUSTOM,
        amount=Decimal("0"),
        status=SubscriptionStatus.ACTIVE,
        started_at=now,
        expired_at=now + timedelta(days=7),
        source=SubscriptionSource.TRIAL,
    )


@pytest.fixture
def slot_repo() -> FakeCalendarSlotRepository:
    return FakeCalendarSlotRepository()


@pytest.fixture
def booking_repo(slot_repo: FakeCalendarSlotRepository) -> FakeBookingRepository:
    return FakeBookingRepository(slot_repo)


@pytest.fixture
def calendar_service(
    slot_repo: FakeCalendarSlotRepository, booking_repo: FakeBookingRepository
) -> CalendarService:
    return CalendarService(
        slot_repo=slot_repo,
        template_repo=FakeSlotTemplateRepository(),
        booking_repo=booking_repo,
    )


async def add_slot(
    slot_repo: FakeCalendarSlotRepository, days_from_today: int, **kwargs
) -> CalendarSlot:
    return await slot_repo.save(
        CalendarSlot(
            trainer_id=1,
            slot_date=get_project_today() + timedelta(days=days_from_today),
            start_time=kwargs.pop("start_time", START),
            end_time=time(11, 0, tzinfo=timezone.utc),
            **kwargs,
        )
    )


class TestCreateBookingLimit:
    @pytest.fixture
    def use_case(
        self,
        calendar_service: CalendarService,
        booking_repo: FakeBookingRepository,
    ) -> CreateBookingUseCase:
        return CreateBookingUseCase(
            calendar_service=calendar_service,
            booking_repo=booking_repo,
            trainer_repo=FakeTrainerRepository([TRAINER]),
            client_repo=FakeClientRepository([CLIENT]),
            pricing_rule_repo=FakeNoneRepository(),
            booking_settings_repo=FakeNoneRepository(),  # дефолтный лимит = 1
            answer_repo=FakeNoneRepository(),
            question_repo=FakeNoneRepository(),
            notification_service=FakeNotificationService(),
            transaction_manager=FakeTransactionManager(),
        )

    async def test_second_own_booking_exceeds_default_limit(
        self,
        use_case: CreateBookingUseCase,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        first = await add_slot(slot_repo, 1)
        second = await add_slot(slot_repo, 2)

        await use_case(CreateBookingRequest(client_id=7, trainer_id=1, slot_id=first.id))
        with pytest.raises(ActiveBookingsLimitExceededException):
            await use_case(
                CreateBookingRequest(client_id=7, trainer_id=1, slot_id=second.id)
            )

    async def test_recurring_occurrences_do_not_count_into_limit(
        self,
        use_case: CreateBookingUseCase,
        slot_repo: FakeCalendarSlotRepository,
        booking_repo: FakeBookingRepository,
    ) -> None:
        recurring_slot = await add_slot(slot_repo, 1)
        own_slot = await add_slot(slot_repo, 2)
        await booking_repo.save(
            Booking(
                client_id=7,
                trainer_id=1,
                slot_id=recurring_slot.id,
                status=BookingStatus.CONFIRMED,
                recurring_booking_id=3,
            )
        )

        booking = await use_case(
            CreateBookingRequest(client_id=7, trainer_id=1, slot_id=own_slot.id)
        )

        assert booking.status == BookingStatus.PENDING


class TestMaintainRecurringBookings:
    @pytest.fixture
    def notifications(self) -> FakeNotificationService:
        return FakeNotificationService()

    def make_use_case(
        self,
        recurring: RecurringBooking,
        slot_repo: FakeCalendarSlotRepository,
        booking_repo: FakeBookingRepository,
        calendar_service: CalendarService,
        notifications: FakeNotificationService,
    ) -> MaintainRecurringBookingsUseCase:
        return MaintainRecurringBookingsUseCase(
            recurring_repo=FakeRecurringBookingRepository([recurring]),
            booking_repo=booking_repo,
            slot_repo=slot_repo,
            calendar_service=calendar_service,
            trainer_repo=FakeTrainerRepository([TRAINER]),
            client_repo=FakeClientRepository([CLIENT]),
            reminder_settings_repo=FakeNoneRepository(),
            pricing_rule_repo=FakeNoneRepository(),
            notification_service=notifications,
            booking_scheduler=FakeBookingScheduler(),
            vacation_repo=FakeNoneRepository(),
            subscription_repo=FakeSubscriptions([active_subscription()]),
            transaction_manager=FakeTransactionManager(),
        )

    def make_recurring(self, weekday: int) -> RecurringBooking:
        return RecurringBooking(
            id=3, trainer_id=1, client_id=7, weekday=weekday, start_time=START
        )

    async def test_cancelled_future_occurrence_is_not_recreated(
        self,
        slot_repo: FakeCalendarSlotRepository,
        booking_repo: FakeBookingRepository,
        calendar_service: CalendarService,
        notifications: FakeNotificationService,
    ) -> None:
        future_slot = await add_slot(slot_repo, 2)
        recurring = self.make_recurring(future_slot.slot_date.weekday())
        await booking_repo.save(
            Booking(
                client_id=7,
                trainer_id=1,
                slot_id=future_slot.id,
                status=BookingStatus.CANCELLED,
                recurring_booking_id=recurring.id,
            )
        )
        use_case = self.make_use_case(
            recurring, slot_repo, booking_repo, calendar_service, notifications
        )

        await use_case(MaintainRecurringBookingsRequest())

        assert len(booking_repo._bookings) == 1

    async def test_creates_next_week_after_past_occurrence(
        self,
        slot_repo: FakeCalendarSlotRepository,
        booking_repo: FakeBookingRepository,
        calendar_service: CalendarService,
        notifications: FakeNotificationService,
    ) -> None:
        past_slot = await add_slot(slot_repo, -1)
        next_slot = await add_slot(slot_repo, 6)
        recurring = self.make_recurring(past_slot.slot_date.weekday())
        await booking_repo.save(
            Booking(
                client_id=7,
                trainer_id=1,
                slot_id=past_slot.id,
                status=BookingStatus.COMPLETED,
                recurring_booking_id=recurring.id,
            )
        )
        use_case = self.make_use_case(
            recurring, slot_repo, booking_repo, calendar_service, notifications
        )

        await use_case(MaintainRecurringBookingsRequest())

        created = await booking_repo.get_latest_by_recurring_booking_id(recurring.id)
        assert created.slot_id == next_slot.id
        assert created.status == BookingStatus.CONFIRMED

    async def test_vacation_skips_occurrence_silently(
        self,
        slot_repo: FakeCalendarSlotRepository,
        booking_repo: FakeBookingRepository,
        calendar_service: CalendarService,
        notifications: FakeNotificationService,
    ) -> None:
        from src.domain.entities.trainer_vacation import TrainerVacation

        blocked = await add_slot(slot_repo, 6, status=SlotStatus.BLOCKED)
        recurring = self.make_recurring(blocked.slot_date.weekday())
        use_case = self.make_use_case(
            recurring, slot_repo, booking_repo, calendar_service, notifications
        )
        vacation = TrainerVacation(
            trainer_id=1, date_from=blocked.slot_date, date_to=blocked.slot_date
        )

        class Vacations:
            async def get_by_trainer(self, trainer_id, ending_from):
                return [vacation]

        use_case.vacation_repo = Vacations()
        await use_case(MaintainRecurringBookingsRequest())

        # тренер в отпуске — ни записи, ни предупреждения «нет слота»
        assert booking_repo._bookings == {} and notifications.sent == []

    async def test_blocked_slot_notifies_trainer_instead_of_failing(
        self,
        slot_repo: FakeCalendarSlotRepository,
        booking_repo: FakeBookingRepository,
        calendar_service: CalendarService,
        notifications: FakeNotificationService,
    ) -> None:
        blocked = await add_slot(slot_repo, 6, status=SlotStatus.BLOCKED)
        recurring = self.make_recurring(blocked.slot_date.weekday())
        use_case = self.make_use_case(
            recurring, slot_repo, booking_repo, calendar_service, notifications
        )

        await use_case(MaintainRecurringBookingsRequest())

        assert booking_repo._bookings == {}
        assert notifications.sent[0][0] == TRAINER.notification_chat_id

    async def test_no_subscription_skips_silently(
        self,
        slot_repo: FakeCalendarSlotRepository,
        booking_repo: FakeBookingRepository,
        calendar_service: CalendarService,
        notifications: FakeNotificationService,
    ) -> None:
        next_slot = await add_slot(slot_repo, 6)
        recurring = self.make_recurring(next_slot.slot_date.weekday())
        use_case = self.make_use_case(
            recurring, slot_repo, booking_repo, calendar_service, notifications
        )
        use_case.subscription_repo = FakeSubscriptions()

        await use_case(MaintainRecurringBookingsRequest())

        # подписка кончилась — ни записи клиенту, ни сообщений
        assert booking_repo._bookings == {} and notifications.sent == []


class TestPlanNextTrainingReminder:
    """«Запланируйте следующую тренировку» — только если тренер принимает записи."""

    async def make_use_case(self, slot_repo: FakeCalendarSlotRepository, subscriptions):
        past_slot = await add_slot(slot_repo, -4)
        completed = Booking(
            id=1, client_id=7, trainer_id=1, slot_id=past_slot.id,
            status=BookingStatus.COMPLETED,
        )

        class Bookings:
            async def get_upcoming_by_client(self, client_id):
                return []

            async def get_latest_completed_by_client(self, client_id):
                return completed

        class Recurring:
            async def get_active_by_trainer_and_client(self, trainer_id, client_id):
                return None

        class Notifications:
            def __init__(self) -> None:
                self.sent = []

            async def notify_plan_next_training(self, data):
                self.sent.append(data)

        notifications = Notifications()
        use_case = SendPlanNextTrainingReminderUseCase(
            booking_repo=Bookings(),
            slot_repo=slot_repo,
            client_repo=FakeClientRepository([CLIENT]),
            trainer_repo=FakeTrainerRepository([TRAINER]),
            recurring_repo=Recurring(),
            subscription_repo=subscriptions,
            notification_service=notifications,
        )
        return use_case, notifications

    async def test_sent_with_active_subscription(self, slot_repo) -> None:
        use_case, notifications = await self.make_use_case(
            slot_repo, FakeSubscriptions([active_subscription()])
        )
        await use_case(SendPlanNextTrainingReminderRequest(client_id=7))
        assert len(notifications.sent) == 1

    async def test_skipped_without_subscription(self, slot_repo) -> None:
        use_case, notifications = await self.make_use_case(slot_repo, FakeSubscriptions())
        await use_case(SendPlanNextTrainingReminderRequest(client_id=7))
        assert notifications.sent == []
