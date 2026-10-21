from datetime import date
from decimal import Decimal

from sqlalchemy import VARCHAR, Date, Enum as SqlEnum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.client_measurement import ClientMeasurement
from src.domain.enums.booking import BookingActor

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class ClientMeasurementModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "client_measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"), index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    measured_on: Mapped[date] = mapped_column(Date)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    waist: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    chest: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    hips: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    # тот же enum, что у отмены записи: кто внёс замер
    added_by: Mapped[BookingActor] = mapped_column(SqlEnum(BookingActor, name="bookingactor"))

    @classmethod
    def from_entity(cls, entity: ClientMeasurement) -> "ClientMeasurementModel":
        return cls(
            trainer_id=entity.trainer_id,
            client_id=entity.client_id,
            measured_on=entity.measured_on,
            weight=entity.weight,
            waist=entity.waist,
            chest=entity.chest,
            hips=entity.hips,
            photo_file_id=entity.photo_file_id,
            added_by=entity.added_by,
        )

    def to_entity(self) -> ClientMeasurement:
        return ClientMeasurement(
            id=self.id,
            trainer_id=self.trainer_id,
            client_id=self.client_id,
            measured_on=self.measured_on,
            weight=self.weight,
            waist=self.waist,
            chest=self.chest,
            hips=self.hips,
            photo_file_id=self.photo_file_id,
            added_by=self.added_by,
            created_at=self.created_at,
        )
