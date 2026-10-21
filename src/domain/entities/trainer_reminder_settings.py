from dataclasses import dataclass
from datetime import date

from src.domain.constants import DEFAULT_MORNING_DIGEST_HOUR, REMINDER_HOURS_BEFORE_TRAINING
from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class TrainerReminderSettings(Entity):
    trainer_id: int
    hours_before: int = REMINDER_HOURS_BEFORE_TRAINING
    # сводка тренеру в личку: час по времени проекта, None — выключена
    morning_digest_hour: int | None = DEFAULT_MORNING_DIGEST_HOUR
    evening_digest_hour: int | None = None
    # присылать ли сводку, когда тренировок нет («свободный день»)
    digest_on_empty_days: bool = False
    # дата последней отправки — повторный запуск cron в тот же час не дублирует
    last_morning_digest_on: date | None = None
    last_evening_digest_on: date | None = None
