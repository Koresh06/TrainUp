from dataclasses import dataclass

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class FaqItem(Entity):
    question: str
    answer: str
    order: int = 0
    is_active: bool = True
