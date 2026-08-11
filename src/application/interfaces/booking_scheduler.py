from datetime import datetime
from typing import Protocol


class BookingScheduler(Protocol):
    async def schedule_training_reminder(
        self,
        *,
        booking_id: int,
        remind_at_utc: datetime,
    ) -> None: ...

    async def cancel_training_reminder(self, *, booking_id: int) -> None: ...

    async def schedule_plan_next_training_reminder(
        self,
        *,
        client_id: int,
        remind_at_utc: datetime,
    ) -> None: ...
