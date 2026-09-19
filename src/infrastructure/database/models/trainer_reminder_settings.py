from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer

from src.domain.constants import REMINDER_HOURS_BEFORE_TRAINING
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings


from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import TrainerModel


class TrainerReminderSettingsModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "trainer_reminder_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    hours_before: Mapped[int] = mapped_column(
        Integer, default=REMINDER_HOURS_BEFORE_TRAINING
    )

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="reminder_settings",
    )

    @classmethod
    def from_entity(
        cls, entity: "TrainerReminderSettings"
    ) -> "TrainerReminderSettingsModel":
        return cls(
            trainer_id=entity.trainer_id,
            hours_before=entity.hours_before,
        )

    def to_entity(self) -> "TrainerReminderSettings":
        return TrainerReminderSettings(
            id=self.id,
            trainer_id=self.trainer_id,
            hours_before=self.hours_before,
        )

    def update_model(self, entity: "TrainerReminderSettings") -> None:
        self.trainer_id = entity.trainer_id
        self.hours_before = entity.hours_before
