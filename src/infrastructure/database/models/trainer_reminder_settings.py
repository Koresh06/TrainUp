from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer

from src.domain.constants import DEFAULT_MORNING_DIGEST_HOUR, REMINDER_HOURS_BEFORE_TRAINING
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
    morning_digest_hour: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=DEFAULT_MORNING_DIGEST_HOUR
    )
    evening_digest_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    digest_on_empty_days: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    last_morning_digest_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_evening_digest_on: Mapped[date | None] = mapped_column(Date, nullable=True)

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
            morning_digest_hour=entity.morning_digest_hour,
            evening_digest_hour=entity.evening_digest_hour,
            digest_on_empty_days=entity.digest_on_empty_days,
            last_morning_digest_on=entity.last_morning_digest_on,
            last_evening_digest_on=entity.last_evening_digest_on,
        )

    def to_entity(self) -> "TrainerReminderSettings":
        return TrainerReminderSettings(
            id=self.id,
            trainer_id=self.trainer_id,
            hours_before=self.hours_before,
            morning_digest_hour=self.morning_digest_hour,
            evening_digest_hour=self.evening_digest_hour,
            digest_on_empty_days=self.digest_on_empty_days,
            last_morning_digest_on=self.last_morning_digest_on,
            last_evening_digest_on=self.last_evening_digest_on,
        )

    def update_model(self, entity: "TrainerReminderSettings") -> None:
        self.trainer_id = entity.trainer_id
        self.hours_before = entity.hours_before
        self.morning_digest_hour = entity.morning_digest_hour
        self.evening_digest_hour = entity.evening_digest_hour
        self.digest_on_empty_days = entity.digest_on_empty_days
        self.last_morning_digest_on = entity.last_morning_digest_on
        self.last_evening_digest_on = entity.last_evening_digest_on
