from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.program import ProgramRequest
from src.domain.enums.request import RequestStatus
from src.domain.exception.program import ProgramRequestNotFoundException
from src.domain.repositories.program import ProgramRequestRepository
from src.infrastructure.database.models import ProgramRequestModel


class SQLAlchemyProgramRequestRepo(ProgramRequestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[ProgramRequest]:
        query = select(ProgramRequestModel)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, program_request_id: int) -> ProgramRequest | None:
        query = select(ProgramRequestModel).where(
            ProgramRequestModel.id == program_request_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, program_request: ProgramRequest) -> ProgramRequest:
        if program_request.id == 0:
            model = ProgramRequestModel.from_entity(program_request)
            self._session.add(model)
        else:
            query = select(ProgramRequestModel).where(
                ProgramRequestModel.id == program_request.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise ProgramRequestNotFoundException(
                    program_request_id=program_request.id
                )
            model.update_model(program_request)

        await self._session.flush()
        return model.to_entity()

    async def delete(self, program_request_id: int) -> None:
        query = select(ProgramRequestModel).where(
            ProgramRequestModel.id == program_request_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise ProgramRequestNotFoundException(program_request_id=program_request_id)
        await self._session.delete(model)
        await self._session.flush()

    async def get_by_trainer_id(
        self, trainer_id: int, statuses: list[RequestStatus]
    ) -> list[ProgramRequest]:
        query = (
            select(ProgramRequestModel)
            .where(
                ProgramRequestModel.trainer_id == trainer_id,
                ProgramRequestModel.status.in_(statuses),
            )
            .order_by(ProgramRequestModel.created_at.desc())
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def count_by_trainer_created_between(
        self, created_from: datetime, created_to: datetime
    ) -> dict[int, int]:
        query = (
            select(ProgramRequestModel.trainer_id, func.count())
            .where(
                ProgramRequestModel.created_at >= created_from,
                ProgramRequestModel.created_at < created_to,
            )
            .group_by(ProgramRequestModel.trainer_id)
        )
        result = await self._session.execute(query)
        return dict(result.all())
