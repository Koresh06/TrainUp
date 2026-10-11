from dataclasses import dataclass

from src.domain.entities.base import Entity
from src.domain.enums.request import RequestStatus


@dataclass(kw_only=True)
class FeedbackMessage(Entity):
    client_id: int
    trainer_id: int
    phone: str | None    # заполнен — просьба перезвонить
    message: str | None  # заполнен — сообщение тренеру
    status: RequestStatus = RequestStatus.NEW

    def is_callback_request(self) -> bool:
        return self.message is None
