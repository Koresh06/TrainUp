from dataclasses import dataclass
from datetime import date

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class TrainerVacation(Entity):
    """Отпуск/больничный: все слоты периода закрыты, в том числе те, что
    календарь сгенерирует позже, а постоянные тренировки не создаются."""

    trainer_id: int
    date_from: date
    date_to: date
    note: str | None = None

    def covers(self, day: date) -> bool:
        return self.date_from <= day <= self.date_to
