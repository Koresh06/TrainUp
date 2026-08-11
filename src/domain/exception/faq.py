from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class FaqItemNotFoundException(DomainError):
    faq_id: int

    @property
    def message(self) -> str:
        return f"FAQ с id {self.faq_id} не найден"
