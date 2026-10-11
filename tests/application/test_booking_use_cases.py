from datetime import time, timedelta, timezone

import pytest

from src.application.use_cases.booking.create import (
    CreateBookingRequest,
    CreateBookingUseCase,
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
from src.domain.enums.booking import BookingStatus
from src.domain.enums.slot import SlotStatus
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
