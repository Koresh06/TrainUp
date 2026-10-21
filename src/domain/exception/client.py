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


@dataclass
class ClientAlreadyHasTelegramException(DomainError):
    client_id: int

    @property
    def message(self) -> str:
        return f"Карточка клиента {self.client_id} уже привязана к Telegram"


@dataclass
class ClientInviteNotFoundException(DomainError):
    token: str

    @property
    def message(self) -> str:
        return "Персональная ссылка клиента недействительна"


@dataclass
class ClientHasBookingsException(DomainError):
    client_id: int

    @property
    def message(self) -> str:
        return f"У клиента {self.client_id} есть записи — удалить карточку нельзя"


@dataclass
class ClientAccessDeniedException(DomainError):
    """Тренер пытается работать с чужим клиентом."""

    client_id: int
    trainer_id: int

    @property
    def message(self) -> str:
        return f"Клиент {self.client_id} не принадлежит тренеру {self.trainer_id}"
