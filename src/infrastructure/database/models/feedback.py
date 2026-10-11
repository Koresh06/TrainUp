from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey,
    Integer,
    VARCHAR,
    Enum as SqlEnum,
)

from src.domain.entities.feedback import FeedbackMessage
from src.domain.enums.request import RequestStatus

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import ClientModel, TrainerModel


class FeedbackMessageModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "feedback_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        index=True,
    )
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    message: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        SqlEnum(RequestStatus),
        default=RequestStatus.NEW,
        server_default=RequestStatus.NEW.name,
    )

    client: Mapped["ClientModel"] = relationship(
        "ClientModel",
        back_populates="feedback_messages",
    )
    trainer: Mapped["TrainerModel"] = relationship("TrainerModel")

    @classmethod
    def from_entity(cls, entity: "FeedbackMessage") -> "FeedbackMessageModel":
        return cls(
            client_id=entity.client_id,
            trainer_id=entity.trainer_id,
            phone=entity.phone,
            message=entity.message,
            status=entity.status,
        )

    def to_entity(self) -> "FeedbackMessage":
        return FeedbackMessage(
            id=self.id,
            client_id=self.client_id,
            trainer_id=self.trainer_id,
            phone=self.phone,
            message=self.message,
            status=self.status,
            created_at=self.created_at,
        )

    def update_model(self, entity: "FeedbackMessage") -> None:
        self.client_id = entity.client_id
        self.trainer_id = entity.trainer_id
        self.phone = entity.phone
        self.message = entity.message
        self.status = entity.status
