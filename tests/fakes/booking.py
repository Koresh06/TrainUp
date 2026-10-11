from datetime import datetime

from src.domain.entities.booking import Booking
from src.domain.entities.client import Client
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.entities.trainer import Trainer
from src.domain.utils import get_project_today
from tests.fakes.calendar import FakeCalendarSlotRepository


class FakeBookingRepository:
    """In-memory fake implementing нужную тестам часть BookingRepository."""

    def __init__(self, slot_repo: FakeCalendarSlotRepository) -> None:
        self._bookings: dict[int, Booking] = {}
        self._next_id = 1
        self._slot_repo = slot_repo

    async def get_by_id(self, booking_id: int) -> Booking | None:
        return self._bookings.get(booking_id)

    async def count_active_by_slot_id(self, slot_id: int) -> int:
        return sum(
            1 for b in self._bookings.values() if b.slot_id == slot_id and b.is_active()
        )

    async def count_active_by_slot_ids(self, slot_ids: list[int]) -> dict[int, int]:
        return {
            slot_id: await self.count_active_by_slot_id(slot_id) for slot_id in slot_ids
        }

    async def exists_active_by_client_and_slot(self, client_id: int, slot_id: int) -> bool:
        return any(
            b.client_id == client_id and b.slot_id == slot_id and b.is_active()
            for b in self._bookings.values()
        )

    async def get_upcoming_by_client(self, client_id: int) -> list[Booking]:
        today = get_project_today()
        result = []
        for b in self._bookings.values():
            slot = self._slot_repo._slots.get(b.slot_id)
            if b.client_id == client_id and b.is_active() and slot.slot_date >= today:
                result.append(b)
        return result

    async def get_latest_by_recurring_booking_id(
        self, recurring_booking_id: int
    ) -> Booking | None:
        matching = [
            b
            for b in self._bookings.values()
            if b.recurring_booking_id == recurring_booking_id
        ]
        return max(matching, key=lambda b: b.id) if matching else None

    async def save(self, booking: Booking) -> Booking:
        if booking.id == 0:
            booking.id = self._next_id
            self._next_id += 1
        self._bookings[booking.id] = booking
        return booking


class FakeRecurringBookingRepository:
    def __init__(self, items: list[RecurringBooking] | None = None) -> None:
        self._items = list(items) if items else []

    async def get_all_active(self) -> list[RecurringBooking]:
        return [r for r in self._items if r.is_active]


class FakeTrainerRepository:
    def __init__(self, trainers: list[Trainer]) -> None:
        self._trainers = {t.id: t for t in trainers}

    async def get_by_id(self, trainer_id: int) -> Trainer | None:
        return self._trainers.get(trainer_id)


class FakeClientRepository:
    def __init__(self, clients: list[Client]) -> None:
        self._clients = {c.id: c for c in clients}

    async def get_by_id(self, client_id: int) -> Client | None:
        return self._clients.get(client_id)


class FakeNoneRepository:
    """Репозиторий настроек, у которого для тренера ничего не настроено."""

    async def get_by_trainer_id(self, trainer_id: int) -> None:
        return None

    async def get_all_by_trainer_id(self, trainer_id: int) -> list:
        return []

    async def get_by_client_id(self, client_id: int) -> list:
        return []


class FakeNotificationService:
    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []
        self.new_bookings: list = []

    async def send(self, *, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))

    async def notify_new_booking(self, data) -> None:
        self.new_bookings.append(data)


class FakeBookingScheduler:
    def __init__(self) -> None:
        self.reminders: list[tuple[int, datetime]] = []
        self.completions: list[tuple[int, datetime]] = []

    async def schedule_training_reminder(self, *, booking_id: int, remind_at_utc: datetime) -> None:
        self.reminders.append((booking_id, remind_at_utc))

    async def cancel_training_reminder(self, *, booking_id: int) -> None: ...

    async def schedule_booking_completion(
        self, *, booking_id: int, complete_at_utc: datetime
    ) -> None:
        self.completions.append((booking_id, complete_at_utc))

    async def cancel_booking_completion(self, *, booking_id: int) -> None: ...


class FakeTransactionManager:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None: ...
