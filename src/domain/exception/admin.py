from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class AdminNotFoundException(DomainError):
    tg_id: int

    @property
    def message(self) -> str:
        return f"Админ {self.tg_id} не найден"


@dataclass
class AdminUserNotFoundException(DomainError):
    username: str

    @property
    def message(self) -> str:
        return (
            f"@{self.username} ещё не заходил в бота. Попросите его нажать /start "
            f"или укажите Telegram ID."
        )


@dataclass
class AdminAlreadyExistsException(DomainError):
    tg_id: int

    @property
    def message(self) -> str:
        return f"{self.tg_id} уже администратор"
