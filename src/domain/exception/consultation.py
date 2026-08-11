from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class ConsultationRequestNotFoundException(DomainError):
    consultation_id: int

    @property
    def message(self) -> str:
        return f"Заявка на консультацию с id {self.consultation_id} не найдена"
