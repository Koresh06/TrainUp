from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey,
    Integer,
    VARCHAR,
    DateTime,
    Enum as SqlEnum,
    Numeric,
)

from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingActor, BookingStatus

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        ClientModel,
        TrainerModel,
        CalendarSlotModel,
        RecurringBookingModel,
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
    )
    status: Mapped[BookingStatus] = mapped_column(SqlEnum(BookingStatus))
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    reminder_job_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    recurring_booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("recurring_bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    completion_job_id: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True
    )
    cancelled_by: Mapped[BookingActor | None] = mapped_column(
        SqlEnum(BookingActor, name="bookingactor"), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    package_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_packages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    recurring_booking: Mapped["RecurringBookingModel | None"] = relationship(
        "RecurringBookingModel",
        back_populates="bookings",
    )

    @classmethod
    def from_entity(cls, entity: "Booking") -> "BookingModel":
        return cls(
            client_id=entity.client_id,
            trainer_id=entity.trainer_id,
            slot_id=entity.slot_id,
            status=entity.status,
            price=entity.price,
            reminder_job_id=entity.reminder_job_id,
            recurring_booking_id=entity.recurring_booking_id,
            completion_job_id=entity.completion_job_id,
            cancelled_by=entity.cancelled_by,
            cancelled_at=entity.cancelled_at,
            package_id=entity.package_id,
            paid_at=entity.paid_at,
        )

    def to_entity(self):
        return Booking(
            id=self.id,
            client_id=self.client_id,
            trainer_id=self.trainer_id,
            slot_id=self.slot_id,
            status=self.status,
            price=self.price,
            reminder_job_id=self.reminder_job_id,
            recurring_booking_id=self.recurring_booking_id,
            completion_job_id=self.completion_job_id,
            cancelled_by=self.cancelled_by,
            cancelled_at=self.cancelled_at,
            package_id=self.package_id,
            paid_at=self.paid_at,
            created_at=self.created_at,
        )

    def update_model(self, entity: "Booking") -> None:
        self.client_id = entity.client_id
        self.trainer_id = entity.trainer_id
        self.slot_id = entity.slot_id
        self.status = entity.status
        self.price = entity.price
        self.reminder_job_id = entity.reminder_job_id
        self.recurring_booking_id = entity.recurring_booking_id
        self.completion_job_id = entity.completion_job_id
        self.cancelled_by = entity.cancelled_by
        self.cancelled_at = entity.cancelled_at
        self.package_id = entity.package_id
        self.paid_at = entity.paid_at
