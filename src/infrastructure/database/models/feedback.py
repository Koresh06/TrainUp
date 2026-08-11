from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    DateTime,
    ForeignKey,
    BigInteger,
    Integer,
    VARCHAR,
    Boolean,
    Enum as SqlEnum,
)

from src.domain.entities.feedback import FeedbackMessage

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import ClientModel


class FeedbackMessageModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "feedback_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    message: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    client: Mapped["ClientModel"] = relationship(
        "ClientModel",
        back_populates="feedback_messages",
    )

    @classmethod
    def from_entity(cls, entity: "FeedbackMessage") -> "FeedbackMessageModel":
        return cls(
            client_id=entity.client_id,
            phone=entity.phone,
            message=entity.message,
            is_read=entity.is_read,
        )

    def to_entity(self) -> "FeedbackMessage":
        return FeedbackMessage(
            id=self.id,
            client_id=self.client_id,
            phone=self.phone,
            message=self.message,
            is_read=self.is_read,
        )

    def update_model(self, entity: "FeedbackMessage") -> None:
        self.client_id = entity.client_id
        self.phone = entity.phone
        self.message = entity.message
        self.is_read = entity.is_read
