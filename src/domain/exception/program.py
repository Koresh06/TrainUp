from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class ProgramRequestNotFoundException(DomainError):
    program_request_id: int

    @property
    def message(self) -> str:
        return f"Заявка на программу с id {self.program_request_id} не найдена"
