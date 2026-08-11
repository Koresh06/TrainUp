from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class TrainerNotFoundException(DomainError):
    trainer_id: int | None = None
    tg_id: int | None = None

    @property
    def message(self) -> str:
        if self.tg_id is not None:
            return f"Тренер с tg_id {self.tg_id} не найден"
        return f"Тренер с id {self.trainer_id} не найден"


@dataclass
class TrainerAlreadyExistsException(DomainError):
    tg_id: int

    @property
    def message(self) -> str:
        return f"Тренер с tg_id {self.tg_id} уже существует"
