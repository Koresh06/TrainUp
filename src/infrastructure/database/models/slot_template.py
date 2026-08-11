from datetime import time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey,
    BigInteger,
    Integer,
    VARCHAR,
    Boolean,
    Time,
)

from src.domain.entities.slot_template import SlotTemplate

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
   from src.infrastructure.database.models import TrainerModel



class SlotTemplateModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "slot_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        index=True,
    )
    weekday: Mapped[int] = mapped_column(Integer, index=True)
    start_time: Mapped[time] = mapped_column(Time(timezone=True))
    end_time: Mapped[time] = mapped_column(Time(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="slot_templates",
    )


    @classmethod
    def from_entity(cls, entity: "SlotTemplate") -> "SlotTemplateModel":
        return cls(
            trainer_id=entity.trainer_id,
            weekday=entity.weekday,
            start_time=entity.start_time,
            end_time=entity.end_time,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "SlotTemplate":
        return SlotTemplate(
            id=self.id,
            trainer_id=self.trainer_id,
            weekday=self.weekday,
            start_time=self.start_time,
            end_time=self.end_time,
            is_active=self.is_active,
        )
    
    def update_model(self, entity: "SlotTemplate") -> None:
        self.trainer_id = entity.trainer_id
        self.weekday = entity.weekday
        self.start_time = entity.start_time
        self.end_time = entity.end_time
        self.is_active = entity.is_active

