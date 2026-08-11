from datetime import time, date
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
    Date,
    Enum as SqlEnum,
    UniqueConstraint,
)

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.enums.slot import SlotStatus, SlotSource

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import TrainerModel, BookingModel


class CalendarSlotModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "calendar_slots"
    __table_args__ = (
        UniqueConstraint(
            "trainer_id",
            "slot_date",
            "start_time",
            name="uq_slot_trainer_date_start",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        index=True,
    )
    slot_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time(timezone=True))
    end_time: Mapped[time] = mapped_column(Time(timezone=True))
    status: Mapped[SlotStatus] = mapped_column(
        SqlEnum(SlotStatus),
        index=True,
    )
    source: Mapped[SlotSource] = mapped_column(SqlEnum(SlotSource))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="calendar_slots",
    )
    booking: Mapped["BookingModel | None"] = relationship(
        "BookingModel",
        back_populates="slot",
        uselist=False,
    )

    @classmethod
    def from_entity(cls, entity: "CalendarSlot") -> "CalendarSlotModel":
        return cls(
            trainer_id=entity.trainer_id,
            slot_date=entity.slot_date,
            start_time=entity.start_time,
            end_time=entity.end_time,
            status=entity.status,
            source=entity.source,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "CalendarSlot":
        return CalendarSlot(
            id=self.id,
            trainer_id=self.trainer_id,
            slot_date=self.slot_date,
            start_time=self.start_time,
            end_time=self.end_time,
            status=self.status,
            source=self.source,
            is_active=self.is_active,
        )

    def update_model(self, entity: "CalendarSlot") -> None:
        self.trainer_id = entity.trainer_id
        self.slot_date = entity.slot_date
        self.start_time = entity.start_time
        self.end_time = entity.end_time
        self.status = entity.status
        self.source = entity.source
        self.is_active = entity.is_active
