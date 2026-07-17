from typing import Protocol

from src.domain.entities.feedback import FeedbackMessage


class FeedbackRepository(Protocol):
    async def save(self, feedback) -> FeedbackMessage:
        ...