from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class TrainerInviteLinkNotFoundException(DomainError):
    invite_link_id: int | None = None
    token: str | None = None

    @property
    def message(self) -> str:
        if self.token is not None:
            return f"Инвайт-ссылка с токеном {self.token} не найдена"
        return f"Инвайт-ссылка с id {self.invite_link_id} не найдена"


@dataclass
class TrainerInviteLinkAlreadyExistsException(DomainError):
    token: str

    @property
    def message(self) -> str:
        return f"Инвайт-ссылка с токеном {self.token} уже существует"


@dataclass
class TrainerInviteLinkInactiveException(DomainError):
    token: str

    @property
    def message(self) -> str:
        return f"Инвайт-ссылка с токеном {self.token} больше не активна"