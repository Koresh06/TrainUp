from datetime import date
from typing import Protocol

from src.domain.entities.trainer_vacation import TrainerVacation


class TrainerVacationRepository(Protocol):
    async def get_by_id(self, vacation_id: int) -> TrainerVacation | None: ...

    async def get_by_trainer(self, trainer_id: int, ending_from: date) -> list[TrainerVacation]:
        """Периоды, которые ещё не закончились к ending_from."""
        ...

    async def save(self, vacation: TrainerVacation) -> TrainerVacation: ...

    async def delete(self, vacation_id: int) -> None: ...
