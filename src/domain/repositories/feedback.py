from datetime import datetime
from typing import Protocol

from src.domain.entities.feedback import FeedbackMessage
from src.domain.enums.request import RequestStatus


class FeedbackRepository(Protocol):
    async def get_all(self) -> list[FeedbackMessage]:
        ...

    async def get_by_id(self, feedback_id: int) -> FeedbackMessage | None:
        ...

    async def save(self, feedback) -> FeedbackMessage:
        ...

    async def get_by_trainer_id(
        self, trainer_id: int, statuses: list[RequestStatus]
    ) -> list[FeedbackMessage]:
        ...

    async def count_by_trainer_created_between(
        self, created_from: datetime, created_to: datetime
    ) -> dict[int, int]:
        ...
