from datetime import date, time, timedelta

import pytest

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.slot_template import SlotTemplate
from src.domain.enums.slot import SlotSource, SlotStatus
from src.domain.exception.booking import SlotAlreadyBookedException
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.services.calendar_service import CalendarService
from tests.fakes.calendar import FakeCalendarSlotRepository, FakeSlotTemplateRepository

TRAINER_ID = 1
OTHER_TRAINER_ID = 2


def other_weekday(weekday: int) -> int:
    """A weekday guaranteed to differ from `weekday`."""
    return (weekday + 3) % 7


@pytest.fixture
def slot_repo() -> FakeCalendarSlotRepository:
    return FakeCalendarSlotRepository()


@pytest.fixture
def template_repo() -> FakeSlotTemplateRepository:
    return FakeSlotTemplateRepository()


@pytest.fixture
def service(
    slot_repo: FakeCalendarSlotRepository,
    template_repo: FakeSlotTemplateRepository,
) -> CalendarService:
    return CalendarService(slot_repo=slot_repo, template_repo=template_repo)


def make_template(
    trainer_id: int,
    weekday: int,
    start: time,
    end: time,
    is_active: bool = True,
) -> SlotTemplate:
    return SlotTemplate(
        trainer_id=trainer_id,
        weekday=weekday,
        start_time=start,
        end_time=end,
        is_active=is_active,
    )


def make_slot(
    trainer_id: int,
    slot_date: date,
    start: time = time(10, 0),
    end: time = time(11, 0),
    status: SlotStatus = SlotStatus.FREE,
    source: SlotSource = SlotSource.MANUAL,
) -> CalendarSlot:
    return CalendarSlot(
        trainer_id=trainer_id,
        slot_date=slot_date,
        start_time=start,
        end_time=end,
        status=status,
        source=source,
    )


class TestGenerateSlotsForPeriod:
    async def test_creates_slots_only_for_matching_weekday_in_range(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
        template_repo: FakeSlotTemplateRepository,
    ) -> None:
        today = date.today()
        weekday_a = today.weekday()
        weekday_b = other_weekday(weekday_a)

        template_repo._templates.append(
            make_template(TRAINER_ID, weekday_a, time(10, 0), time(11, 0))
        )
        template_repo._templates.append(
            make_template(TRAINER_ID, weekday_b, time(14, 0), time(15, 0))
        )

        days_ahead = 6
        result = await service.generate_slots_for_period(TRAINER_ID, days_ahead)

        expected_dates_a = [
            today + timedelta(days=offset)
            for offset in range(days_ahead + 1)
            if (today + timedelta(days=offset)).weekday() == weekday_a
        ]
        expected_dates_b = [
            today + timedelta(days=offset)
            for offset in range(days_ahead + 1)
            if (today + timedelta(days=offset)).weekday() == weekday_b
        ]

        assert len(result) == len(expected_dates_a) + len(expected_dates_b)

        slots_a = [s for s in result if s.start_time == time(10, 0)]
        slots_b = [s for s in result if s.start_time == time(14, 0)]

        assert sorted(s.slot_date for s in slots_a) == sorted(expected_dates_a)
        assert sorted(s.slot_date for s in slots_b) == sorted(expected_dates_b)
        assert all(s.trainer_id == TRAINER_ID for s in result)
        assert all(s.status == SlotStatus.FREE for s in result)
        assert all(s.source == SlotSource.TEMPLATE for s in result)

    async def test_ignores_inactive_templates(
        self,
        service: CalendarService,
        template_repo: FakeSlotTemplateRepository,
    ) -> None:
        today = date.today()
        template_repo._templates.append(
            make_template(
                TRAINER_ID, today.weekday(), time(10, 0), time(11, 0), is_active=False
            )
        )

        result = await service.generate_slots_for_period(TRAINER_ID, 0)

        assert result == []

    async def test_second_call_is_idempotent(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
        template_repo: FakeSlotTemplateRepository,
    ) -> None:
        today = date.today()
        template_repo._templates.append(
            make_template(TRAINER_ID, today.weekday(), time(10, 0), time(11, 0))
        )

        first_result = await service.generate_slots_for_period(TRAINER_ID, 0)
        assert len(first_result) == 1
        assert len(slot_repo._slots) == 1

        second_result = await service.generate_slots_for_period(TRAINER_ID, 0)
        assert second_result == []
        assert len(slot_repo._slots) == 1

    async def test_no_templates_returns_empty_and_does_not_call_save_many(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        result = await service.generate_slots_for_period(TRAINER_ID, 5)

        assert result == []
        assert slot_repo.save_many_call_count == 0

    async def test_multiple_templates_same_weekday_both_created(
        self,
        service: CalendarService,
        template_repo: FakeSlotTemplateRepository,
    ) -> None:
        today = date.today()
        weekday = today.weekday()
        template_repo._templates.append(
            make_template(TRAINER_ID, weekday, time(10, 0), time(11, 0))
        )
        template_repo._templates.append(
            make_template(TRAINER_ID, weekday, time(18, 0), time(19, 0))
        )

        result = await service.generate_slots_for_period(TRAINER_ID, 0)

        assert len(result) == 2
        assert all(s.slot_date == today for s in result)
        start_times = {s.start_time for s in result}
        assert start_times == {time(10, 0), time(18, 0)}


class TestGetFreeSlots:
    async def test_returns_only_free_status_slots(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        today = date.today()
        await slot_repo.save(make_slot(TRAINER_ID, today, status=SlotStatus.FREE))
        await slot_repo.save(make_slot(TRAINER_ID, today, status=SlotStatus.BOOKED))
        await slot_repo.save(make_slot(TRAINER_ID, today, status=SlotStatus.BLOCKED))

        result = await service.get_free_slots(TRAINER_ID, 0)

        assert len(result) == 1
        assert result[0].status == SlotStatus.FREE

    async def test_excludes_other_trainer_slots(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        today = date.today()
        await slot_repo.save(make_slot(TRAINER_ID, today, status=SlotStatus.FREE))
        await slot_repo.save(make_slot(OTHER_TRAINER_ID, today, status=SlotStatus.FREE))

        result = await service.get_free_slots(TRAINER_ID, 0)

        assert len(result) == 1
        assert all(s.trainer_id == TRAINER_ID for s in result)

    async def test_excludes_dates_beyond_days_ahead(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        today = date.today()
        in_range = await slot_repo.save(
            make_slot(TRAINER_ID, today + timedelta(days=2), status=SlotStatus.FREE)
        )
        out_of_range = await slot_repo.save(
            make_slot(TRAINER_ID, today + timedelta(days=5), status=SlotStatus.FREE)
        )

        result = await service.get_free_slots(TRAINER_ID, 3)

        result_ids = {s.id for s in result}
        assert in_range.id in result_ids
        assert out_of_range.id not in result_ids


class TestBookSlot:
    async def test_books_free_slot(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        slot = await slot_repo.save(
            make_slot(TRAINER_ID, date.today(), status=SlotStatus.FREE)
        )

        result = await service.book_slot(slot.id)

        assert result.status == SlotStatus.BOOKED
        stored = await slot_repo.get_by_id(slot.id)
        assert stored is not None
        assert stored.status == SlotStatus.BOOKED

    async def test_raises_when_slot_not_found(
        self,
        service: CalendarService,
    ) -> None:
        with pytest.raises(CalendarSlotNotFoundException):
            await service.book_slot(999)

    async def test_raises_when_slot_already_booked(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        slot = await slot_repo.save(
            make_slot(TRAINER_ID, date.today(), status=SlotStatus.BOOKED)
        )

        with pytest.raises(SlotAlreadyBookedException):
            await service.book_slot(slot.id)


class TestReleaseSlot:
    async def test_releases_booked_slot_back_to_free(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        slot = await slot_repo.save(
            make_slot(TRAINER_ID, date.today(), status=SlotStatus.BOOKED)
        )

        result = await service.release_slot(slot.id)

        assert result.status == SlotStatus.FREE

    async def test_release_updates_updated_at(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
    ) -> None:
        slot = await slot_repo.save(
            make_slot(TRAINER_ID, date.today(), status=SlotStatus.BOOKED)
        )
        updated_at_before = slot.updated_at

        result = await service.release_slot(slot.id)

        assert result.updated_at > updated_at_before

    async def test_raises_when_slot_not_found(
        self,
        service: CalendarService,
    ) -> None:
        with pytest.raises(CalendarSlotNotFoundException):
            await service.release_slot(999)


class TestBlockSlot:
    @pytest.mark.parametrize(
        "initial_status",
        [SlotStatus.FREE, SlotStatus.BOOKED],
    )
    async def test_blocks_slot_from_any_previous_status(
        self,
        service: CalendarService,
        slot_repo: FakeCalendarSlotRepository,
        initial_status: SlotStatus,
    ) -> None:
        slot = await slot_repo.save(
            make_slot(TRAINER_ID, date.today(), status=initial_status)
        )

        result = await service.block_slot(slot.id)

        assert result.status == SlotStatus.BLOCKED

    async def test_raises_when_slot_not_found(
        self,
        service: CalendarService,
    ) -> None:
        with pytest.raises(CalendarSlotNotFoundException):
            await service.block_slot(999)
