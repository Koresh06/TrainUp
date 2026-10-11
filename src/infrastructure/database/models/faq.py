
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    Integer,
    Boolean,
    Enum as SqlEnum,
    TEXT,
)

from src.domain.entities.faq import FaqItem
from src.domain.enums.faq import FaqAudience

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class FaqItemModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "faq_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(TEXT)
    answer: Mapped[str] = mapped_column(TEXT)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    audience: Mapped[FaqAudience] = mapped_column(
        SqlEnum(FaqAudience),
        default=FaqAudience.CLIENT,
        server_default=FaqAudience.CLIENT.name,
        index=True,
    )

    @classmethod
    def from_entity(cls, entity: "FaqItem") -> "FaqItemModel":
        return cls(
            question=entity.question,
            answer=entity.answer,
            order=entity.order,
            is_active=entity.is_active,
            audience=entity.audience,
        )

    def to_entity(self) -> "FaqItem":
        return FaqItem(
            id=self.id,
            question=self.question,
            answer=self.answer,
            order=self.order,
            is_active=self.is_active,
            audience=self.audience,
        )

    def update_model(self, entity: "FaqItem") -> None:
        self.question = entity.question
        self.answer = entity.answer
        self.order = entity.order
        self.is_active = entity.is_active
        self.audience = entity.audience
