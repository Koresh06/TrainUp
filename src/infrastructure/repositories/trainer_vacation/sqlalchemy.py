from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trainer_vacation import TrainerVacation
from src.domain.repositories.trainer_vacation import TrainerVacationRepository
from src.infrastructure.database.models import TrainerVacationModel


class SQLAlchemyTrainerVacationRepo(TrainerVacationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, vacation_id: int) -> TrainerVacation | None:
        model = await self._session.get(TrainerVacationModel, vacation_id)
        return model.to_entity() if model is not None else None

    async def get_by_trainer(self, trainer_id: int, ending_from: date) -> list[TrainerVacation]:
        query = (
            select(TrainerVacationModel)
            .where(
                TrainerVacationModel.trainer_id == trainer_id,
                TrainerVacationModel.date_to >= ending_from,
            )
            .order_by(TrainerVacationModel.date_from)
        )
        result = await self._session.execute(query)
        return [m.to_entity() for m in result.scalars().all()]

    async def save(self, vacation: TrainerVacation) -> TrainerVacation:
        model = TrainerVacationModel.from_entity(vacation)
        self._session.add(model)
        await self._session.flush()
        return model.to_entity()

    async def delete(self, vacation_id: int) -> None:
        await self._session.execute(
            delete(TrainerVacationModel).where(TrainerVacationModel.id == vacation_id)
        )
        await self._session.flush()
