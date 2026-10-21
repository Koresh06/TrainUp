from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from typing import Protocol

from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus


@dataclass(frozen=True)
class BookingStatRow:
    """Плоская строка «запись + дата/время слота» для статистики и графиков —
    чтобы не тянуть сущности и не делать N запросов за слотами."""

    booking_id: int
    trainer_id: int
    client_id: int
    status: BookingStatus
    price: Decimal | None
    slot_date: date
    start_time: time
    rating: int | None = None


@dataclass(frozen=True)
class BookingView:
    """Запись вместе со слотом и клиентом — для экранов тренера (расписание,
    история, карточка клиента): один JOIN вместо двух запросов на каждую бронь."""

    booking: Booking
    slot_date: date
    start_time: time
    client_first_name: str
    client_last_name: str | None
    client_has_telegram: bool

    @property
    def client_short_name(self) -> str:
        if self.client_last_name:
            return f"{self.client_first_name} {self.client_last_name[0]}."
        return self.client_first_name

    @property
    def client_full_name(self) -> str:
        return f"{self.client_first_name} {self.client_last_name or ''}".strip()


class BookingRepository(Protocol):
    async def get_all(self) -> list[Booking]: ...

    async def get_by_id(self, booking_id: int) -> Booking | None: ...

    async def get_upcoming_by_client(self, client_id: int) -> list[Booking]: ...

    async def get_upcoming_by_trainer(self, trainer_id: int) -> list[Booking]: ...

    async def count_active_by_slot_id(self, slot_id: int) -> int: ...

    async def count_active_by_slot_ids(self, slot_ids: list[int]) -> dict[int, int]: ...

    async def exists_active_by_client_and_slot(
        self, client_id: int, slot_id: int
    ) -> bool: ...

    async def save(self, booking: Booking) -> Booking: ...

    async def delete(self, booking_id: int) -> None: ...

    async def get_latest_by_recurring_booking_id(
        self, recurring_booking_id: int
    ) -> Booking | None: ...

    async def get_upcoming_by_recurring_booking_id(
        self, recurring_booking_id: int
    ) -> list[Booking]: ...

    async def get_past_confirmed(self, before_date: date) -> list[Booking]: ...

    async def get_latest_completed_by_client(self, client_id: int) -> Booking | None: ...

    async def count_completed_by_trainer_in_period(
        self,
        trainer_id: int,
        date_from: date,
        date_to: date,
    ) -> int: ...
    
    async def count_cancelled_by_trainer_in_period(
        self,
        trainer_id: int,
        date_from: date,
        date_to: date,
    ) -> int: ...

    async def count_by_trainer_and_status(
        self, date_from: date, date_to: date
    ) -> dict[tuple[int, BookingStatus], int]: ...

    async def get_views(
        self,
        *,
        trainer_id: int,
        date_from: date | None = None,
        date_to: date | None = None,
        statuses: tuple[BookingStatus, ...] | None = None,
        client_id: int | None = None,
        newest_first: bool = False,
        limit: int | None = None,
    ) -> list[BookingView]:
        """Записи тренера с датой слота в [date_from; date_to] (границы опциональны)."""
        ...

    async def has_any_by_client(self, client_id: int) -> bool: ...

    async def get_stat_rows(
        self, date_from: date, date_to: date, trainer_id: int | None = None
    ) -> list[BookingStatRow]:
        """Записи с датой слота в [date_from; date_to]; trainer_id=None — все тренеры."""
        ...
