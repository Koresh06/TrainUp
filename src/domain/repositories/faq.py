from typing import Protocol

from src.domain.entities.faq import FaqItem


class FaqRepository(Protocol):
    async def get_all(self) -> list[FaqItem]:
        ...

    async def get_by_id(self, faq_id: int) -> FaqItem | None:
        ...

    async def save(self, faq_item: FaqItem) -> FaqItem:
        ...

    async def get_active(self) -> list[FaqItem]:
        ...