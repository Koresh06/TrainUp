from dataclasses import dataclass

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class FeedbackMessage(Entity):
    client_id: int
    phone: str | None
    message: str | None
    is_read: bool = False

    def mark_as_read(self) -> None:
        self.is_read = True