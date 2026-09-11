from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    TIME,
    ForeignKey,
    ForeignKey,
    Integer,
    Boolean,
)

from src.domain.entities.recurring_booking import RecurringBooking


from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        ClientModel,
        TrainerModel,
        BookingModel,
    )


class RecurringBookingModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "recurring_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        index=True,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        index=True,
    )
    weekday: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[time] = mapped_column(TIME(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="recurring_bookings",
    )
    client: Mapped["ClientModel"] = relationship(
        "ClientModel",
        back_populates="recurring_bookings",
    )
    bookings: Mapped[list["BookingModel"]] = relationship(
        "BookingModel",
        back_populates="recurring_booking",
    )

    @classmethod
    def from_entity(cls, entity: "RecurringBooking") -> "RecurringBookingModel":
        return cls(
            trainer_id=entity.trainer_id,
            client_id=entity.client_id,
            weekday=entity.weekday,
            start_time=entity.start_time,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "RecurringBooking":
        return RecurringBooking(
            id=self.id,
            trainer_id=self.trainer_id,
            client_id=self.client_id,
            weekday=self.weekday,
            start_time=self.start_time,
            is_active=self.is_active,
        )

    def update_model(self, entity: "RecurringBooking") -> None:
        self.trainer_id = entity.trainer_id
        self.client_id = entity.client_id
        self.weekday = entity.weekday
        self.start_time = entity.start_time
        self.is_active = entity.is_active