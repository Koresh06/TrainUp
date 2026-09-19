from dataclasses import dataclass

from src.domain.constants import REMINDER_HOURS_BEFORE_TRAINING
from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class TrainerReminderSettings(Entity):
    trainer_id: int
    hours_before: int = REMINDER_HOURS_BEFORE_TRAINING