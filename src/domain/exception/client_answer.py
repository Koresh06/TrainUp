from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class ClientAnswerNotFoundException(DomainError):
    client_answer_id: str

    @property
    def message(self) -> str:
        return f"Client answer with id {self.client_answer_id} not found"