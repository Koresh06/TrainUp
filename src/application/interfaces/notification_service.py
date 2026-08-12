from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class NewBookingNotificationDTO:
    chat_id: int
    booking_id: int
    date_label: str
    time_label: str
    client_first_name: str
    client_last_name: str | None
    client_username: str | None
    client_phone: str
    client_age: int


class NotificationService(Protocol):
    async def send(self, *, chat_id: int, text: str) -> None: ...

    async def notify_new_booking(self, data: NewBookingNotificationDTO) -> None: ...