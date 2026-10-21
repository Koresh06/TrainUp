from dataclasses import dataclass

from src.domain.enums.booking import BookingStatus
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


@dataclass
class BookingStatusTransitionException(DomainError):
    booking_id: int
    status: BookingStatus

    @property
    def message(self) -> str:
        return (
            f"Запись с id {self.booking_id} в статусе {self.status.value} "
            f"нельзя перевести в новый статус"
        )


@dataclass
class ActiveBookingsLimitExceededException(DomainError):
    client_id: int
    limit: int

    @property
    def message(self) -> str:
        return (
            f"У клиента с id {self.client_id} уже {self.limit} активных записей "
            f"— это максимум"
        )


@dataclass
class TrainingNotStartedException(DomainError):
    booking_id: int

    @property
    def message(self) -> str:
        return f"Тренировка по записи {self.booking_id} ещё не началась"
