from typing import Protocol

from src.domain.entities.feedback import FeedbackMessage


class FeedbackRepository(Protocol):
    async def get_all(self) -> list[FeedbackMessage]:
        ...

    async def get_by_id(self, feedback_id: int) -> FeedbackMessage | None:
        ...

    async def get_unread(self) -> list[FeedbackMessage]:
        ...

    async def save(self, feedback) -> FeedbackMessage:
        ...