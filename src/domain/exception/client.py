from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class AssigningClientToAnotherTrainerError(DomainError):
    client_id: int
    trainer_id: int
    
    @property
    def message(self) -> str:
        return f"Клиент с id {self.client_id} уже назначен другому тренеру с id {self.trainer_id}"
    