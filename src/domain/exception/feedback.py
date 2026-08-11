from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class FeedbackNotFoundException(DomainError):
    feedback_id: int

    @property
    def message(self) -> str:
        return f"Обращение с id {self.feedback_id} не найдено"
