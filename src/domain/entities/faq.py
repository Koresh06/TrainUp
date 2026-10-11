from dataclasses import dataclass

from src.domain.entities.base import Entity
from src.domain.enums.faq import FaqAudience


@dataclass(kw_only=True)
class FaqItem(Entity):
    question: str
    answer: str
    order: int = 0 # поле для сортировки
    is_active: bool = True
    audience: FaqAudience = FaqAudience.CLIENT
