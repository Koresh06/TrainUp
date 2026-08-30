from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    ARRAY,
    ForeignKey,
    Integer,
    VARCHAR,
)

from src.domain.entities.client_answer import ClientAnswer

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class ClientAnswerModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "client_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("registration_questions.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[list[str]] = mapped_column(ARRAY(VARCHAR(1000)))

    @classmethod
    def from_entity(cls, entity: "ClientAnswer") -> "ClientAnswerModel":
        return cls(
            client_id=entity.client_id,
            question_id=entity.question_id,
            value=entity.value,
        )

    def to_entity(self) -> "ClientAnswer":
        return ClientAnswer(
            id=self.id,
            client_id=self.client_id,
            question_id=self.question_id,
            value=self.value,
        )

    def update_model(self, entity: "ClientAnswer") -> None:
        self.client_id = entity.client_id
        self.question_id = entity.question_id
        self.value = entity.value
