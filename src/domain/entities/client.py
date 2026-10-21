from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.base import Entity
from src.domain.enums.client import ClientSource
from src.domain.enums.training import SportExperience
from src.domain.exception.client import (
    AssigningClientToAnotherTrainerError,
    ClientAlreadyHasTelegramException,
)


@dataclass(kw_only=True)
class Client(Entity):
    # None — клиент без Telegram (тренер завёл карточку вручную): бот ему
    # ничего не пишет, карточка нужна тренеру для учёта и расписания
    tg_id: int | None = None
    trainer_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None
    age: int | None = None
    sport_experience: SportExperience | None = None
    is_active: bool = True
    source: ClientSource = ClientSource.TELEGRAM
    # заметка тренера о клиенте («колено, без прыжков») — клиент её не видит
    trainer_note: str | None = None
    # токен персональной ссылки: по ней человек «забирает» свою карточку,
    # когда приходит в бота, — история тренировок сохраняется
    invite_token: str | None = None
    # реферальная программа: свой код для ссылки «пригласить друга»,
    # кто пригласил этого клиента и когда пригласившему начислен бонус
    referral_code: str | None = None
    referred_by_client_id: int | None = None
    referral_rewarded_at: datetime | None = None

    @property
    def has_telegram(self) -> bool:
        return self.tg_id is not None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name or ''}".strip()

    @property
    def short_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name[0]}."
        return self.first_name

    def assingn_trainer(self, other_trainer_id: int) -> None:
        if self.trainer_id != other_trainer_id:
            raise AssigningClientToAnotherTrainerError(
                client_id=self.id,
                trainer_id=self.trainer_id,
            )

    def link_telegram(self, *, tg_id: int, username: str | None) -> None:
        """Человек открыл персональную ссылку — карточка становится его аккаунтом."""
        if self.has_telegram:
            raise ClientAlreadyHasTelegramException(client_id=self.id)
        self.tg_id = tg_id
        self.username = username
        self.invite_token = None
        self.touch()
