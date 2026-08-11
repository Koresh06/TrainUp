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
    String,
)

from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_invite_link import TrainerInviteLink

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import TrainerModel


class TrainerInviteLinkModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "trainer_invite_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("trainers.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="invite_links",
    )


    @classmethod
    def from_entity(cls, entity: "TrainerInviteLink") -> "TrainerInviteLinkModel":
        return cls(
            trainer_id=entity.trainer_id,
            token=entity.token,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "TrainerInviteLink":
        return TrainerInviteLink(
            id=self.id,
            trainer_id=self.trainer_id,
            token=self.token,
            is_active=self.is_active,
        )

    def update_model(self, entity: "TrainerInviteLink") -> None:
        self.trainer_id = entity.trainer_id
        self.token = entity.token
        self.is_active = entity.is_active