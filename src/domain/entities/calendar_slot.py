from dataclasses import dataclass
from datetime import date, time

from src.domain.entities.base import Entity
from src.domain.enums.slot import SlotSource, SlotStatus


@dataclass(kw_only=True)
class CalendarSlot(Entity):
    trainer_id: int
    slot_date: date
    start_time: time
    end_time: time
    status: SlotStatus = SlotStatus.FREE
    source: SlotSource = SlotSource.TEMPLATE
    is_active: bool = True

    def is_available(self) -> bool:
        return self.status == SlotStatus.FREE

    def book(self) -> None:
        if not self.is_available():
            raise ValueError("Slot is not available for booking")
        self.status = SlotStatus.BOOKED
        self.touch()

    def release(self) -> None:
        self.status = SlotStatus.FREE
        self.touch()

    def block(self) -> None:
        self.status = SlotStatus.BLOCKED
        self.touch()
