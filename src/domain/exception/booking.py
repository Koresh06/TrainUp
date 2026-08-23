from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class BookingNotFoundException(DomainError):
    booking_id: int

    @property
    def message(self) -> str:
        return f"Запись с id {self.booking_id} не найдена"


@dataclass
class SlotAlreadyBookedException(DomainError):
    slot_id: int

    @property
    def message(self) -> str:
        return f"Слот с id {self.slot_id} уже забронирован"


@dataclass
class ClientAlreadyBookedThisSlotException(DomainError):
    client_id: int
    slot_id: int

    @property
    def message(self) -> str:
        return f"Клиент с id {self.client_id} уже записан на слот с id {self.slot_id}"