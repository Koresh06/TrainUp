from datetime import date

from sqlalchemy import VARCHAR, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.trainer_vacation import TrainerVacation

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class TrainerVacationModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "trainer_vacations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"), index=True
    )
    date_from: Mapped[date] = mapped_column(Date)
    date_to: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)

    @classmethod
    def from_entity(cls, entity: TrainerVacation) -> "TrainerVacationModel":
        return cls(
            trainer_id=entity.trainer_id,
            date_from=entity.date_from,
            date_to=entity.date_to,
            note=entity.note,
        )

    def to_entity(self) -> TrainerVacation:
        return TrainerVacation(
            id=self.id,
            trainer_id=self.trainer_id,
            date_from=self.date_from,
            date_to=self.date_to,
            note=self.note,
            created_at=self.created_at,
        )
