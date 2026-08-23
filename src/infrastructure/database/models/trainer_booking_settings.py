from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer

from src.domain.entities.trainer_booking_settings import TrainerBookingSettings


from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import TrainerModel



class TrainerBookingSettingsModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "trainer_booking_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    calendar_horizon_days: Mapped[int] = mapped_column(Integer)
    max_active_bookings_per_client: Mapped[int] = mapped_column(Integer)

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="booking_settings",
    )

    @classmethod
    def from_entity(cls, entity: "TrainerBookingSettings") -> "TrainerBookingSettingsModel":
        return cls(
            trainer_id=entity.trainer_id,
            calendar_horizon_days=entity.calendar_horizon_days,
            max_active_bookings_per_client=entity.max_active_bookings_per_client,
        )

    def to_entity(self) -> "TrainerBookingSettings":
        return TrainerBookingSettings(
            id=self.id,
            trainer_id=self.trainer_id,
            calendar_horizon_days=self.calendar_horizon_days,
            max_active_bookings_per_client=self.max_active_bookings_per_client,
        )

    def update_model(self, entity: "TrainerBookingSettings") -> None:
        self.trainer_id = entity.trainer_id
        self.calendar_horizon_days = entity.calendar_horizon_days
        self.max_active_bookings_per_client = entity.max_active_bookings_per_client