from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    BigInteger,
    Integer,
    VARCHAR,
    Boolean,
)

from src.domain.entities.trainer import Trainer
from src.infrastructure.database.models.trainer_invite_link import TrainerInviteLinkModel
from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        ClientModel,
        TrainerSubscriptionModel,
        BookingModel,
        CalendarSlotModel,
        SlotTemplateModel,
        TrainerInviteLinkModel,
        ProgramRequestModel,
    )


class TrainerModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    bio: Mapped[str] = mapped_column(VARCHAR(255))
    notification_chat_id: Mapped[int] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    clients: Mapped[list["ClientModel"]] = relationship(
        "ClientModel",
        back_populates="trainer",
    )
    invite_links: Mapped[list["TrainerInviteLinkModel"]] = relationship(
        "TrainerInviteLinkModel",
        back_populates="trainer",
    )
    subscriptions: Mapped[list["TrainerSubscriptionModel"]] = relationship(
        "TrainerSubscriptionModel",
        back_populates="trainer",
    )
    slot_templates: Mapped[list["SlotTemplateModel"]] = relationship(
        "SlotTemplateModel",
        back_populates="trainer",
    )
    calendar_slots: Mapped[list["CalendarSlotModel"]] = relationship(
        "CalendarSlotModel",
        back_populates="trainer",
    )
    bookings: Mapped[list["BookingModel"]] = relationship(
        "BookingModel",
        back_populates="trainer",
    )
    program_requests: Mapped[list["ProgramRequestModel"]] = relationship(
        "ProgramRequestModel",
        back_populates="trainer",
    )


    @classmethod
    def from_entity(cls, entity: "Trainer") -> "TrainerModel":
        return cls(
            tg_id=entity.tg_id,
            name=entity.name,
            bio=entity.bio,
            notification_chat_id=entity.notification_chat_id,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "Trainer":
        return Trainer(
            id=self.id,
            tg_id=self.tg_id,
            name=self.name,
            bio=self.bio,
            notification_chat_id=self.notification_chat_id,
            is_active=self.is_active,
        )

    def update_model(self, entity: "Trainer") -> None:
        self.tg_id = entity.tg_id
        self.name = entity.name
        self.bio = entity.bio
        self.notification_chat_id = entity.notification_chat_id
        self.is_active = entity.is_active
