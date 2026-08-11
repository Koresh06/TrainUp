from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import (
    TrainerAlreadyExistsException,
    TrainerNotFoundException,
)
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.models import TrainerModel


class SQLAlchemyTrainerRepo(TrainerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Trainer]:
        query = select(TrainerModel)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, trainer_id: int) -> Trainer | None:
        query = select(TrainerModel).where(TrainerModel.id == trainer_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_by_tg_id(self, tg_id: int) -> Trainer | None:
        query = select(TrainerModel).where(TrainerModel.tg_id == tg_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_default_active(self) -> Trainer | None:
        query = (
            select(TrainerModel)
            .where(TrainerModel.is_active.is_(True))
            .order_by(TrainerModel.id)
            .limit(1)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, trainer: Trainer) -> Trainer:
        if trainer.id == 0:
            model = TrainerModel.from_entity(trainer)
            self._session.add(model)
        else:
            query = select(TrainerModel).where(TrainerModel.id == trainer.id)
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise TrainerNotFoundException(trainer_id=trainer.id)
            model.update_model(trainer)

        try:
            await self._session.flush()
        except IntegrityError as error:
            await self._session.rollback()
            raise TrainerAlreadyExistsException(tg_id=trainer.tg_id) from error

        return model.to_entity()
