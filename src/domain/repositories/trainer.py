from typing import Protocol

from src.domain.entities.trainer import Trainer


class TrainerRepository(Protocol):
    async def get_by_id(self, trainer_id: int) -> Trainer | None:
        ...

    async def get_by_tg_id(self, tg_id: int) -> Trainer | None:
        ...

    async def get_default_active(self) -> Trainer | None:
        ...

    async def save(self, trainer: Trainer) -> Trainer:
        ...