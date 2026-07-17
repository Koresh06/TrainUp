from typing import Protocol

from src.domain.entities.faq import FaqItem


class FaqRepository(Protocol):
    async def get_active(self) -> list[FaqItem]:
        ...