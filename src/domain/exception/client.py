from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class AssigningClientToAnotherTrainerError(DomainError):
    client_id: int
    trainer_id: int

    @property
    def message(self) -> str:
        return f"Клиент с id {self.client_id} уже назначен другому тренеру с id {self.trainer_id}"


@dataclass
class ClientNotFoundException(DomainError):
    client_id: int | None = None
    tg_id: int | None = None

    @property
    def message(self) -> str:
        if self.tg_id is not None:
            return f"Клиент с tg_id {self.tg_id} не найден"
        return f"Клиент с id {self.client_id} не найден"


@dataclass
class ClientAlreadyExistsException(DomainError):
    tg_id: int

    @property
    def message(self) -> str:
        return f"Клиент с tg_id {self.tg_id} уже существует"
