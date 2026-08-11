from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey,
    DateTime,
    ForeignKey,
    BigInteger,
    Integer,
    VARCHAR,
    Boolean,
    Enum as SqlEnum,
)

from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        ClientModel,
        TrainerModel,
        CalendarSlotModel,
    )


class BookingModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        index=True,
    )
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="RESTRICT"),
        index=True,
    )
    slot_id: Mapped[int] = mapped_column(
        ForeignKey("calendar_slots.id", ondelete="RESTRICT"),
        unique=True,
    )
    status: Mapped[BookingStatus] = mapped_column(SqlEnum(BookingStatus))
    reminder_job_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)

    client: Mapped["ClientModel"] = relationship(
        "ClientModel",
        back_populates="bookings",
    )
    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="bookings",
    )
    slot: Mapped["CalendarSlotModel"] = relationship(
        "CalendarSlotModel",
        back_populates="booking",
    )

    @classmethod
    def from_entity(cls, entity: "Booking") -> "BookingModel":
        return cls(
            client_id=entity.client_id,
            trainer_id=entity.trainer_id,
            slot_id=entity.slot_id,
            status=entity.status,
            reminder_job_id=entity.reminder_job_id,
        )

    def to_entity(self):
        return Booking(
            id=self.id,
            client_id=self.client_id,
            trainer_id=self.trainer_id,
            slot_id=self.slot_id,
            status=self.status,
            reminder_job_id=self.reminder_job_id,
        )

    def update_model(self, entity: "Booking") -> None:
        self.client_id = entity.client_id
        self.trainer_id = entity.trainer_id
        self.slot_id = entity.slot_id
        self.status = entity.status
        self.reminder_job_id = entity.reminder_job_id
