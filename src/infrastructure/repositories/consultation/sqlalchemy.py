from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.consultation import ConsultationRequest
from src.domain.enums.request import RequestStatus
from src.domain.exception.consultation import ConsultationRequestNotFoundException
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.infrastructure.database.models import ConsultationRequestModel


class SQLAlchemyConsultationRequestRepo(ConsultationRequestRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[ConsultationRequest]:
        query = select(ConsultationRequestModel)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, consultation_id: int) -> ConsultationRequest | None:
        query = select(ConsultationRequestModel).where(
            ConsultationRequestModel.id == consultation_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, consultation: ConsultationRequest) -> ConsultationRequest:
        if consultation.id == 0:
            model = ConsultationRequestModel.from_entity(consultation)
            self._session.add(model)
        else:
            query = select(ConsultationRequestModel).where(
                ConsultationRequestModel.id == consultation.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise ConsultationRequestNotFoundException(
                    consultation_id=consultation.id
                )
            model.update_model(consultation)

        await self._session.flush()
        return model.to_entity()

    async def get_by_trainer_id(
        self, trainer_id: int, statuses: list[RequestStatus]
    ) -> list[ConsultationRequest]:
        query = (
            select(ConsultationRequestModel)
            .where(
                ConsultationRequestModel.trainer_id == trainer_id,
                ConsultationRequestModel.status.in_(statuses),
            )
            .order_by(ConsultationRequestModel.created_at.desc())
        )
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def count_by_trainer_created_between(
        self, created_from: datetime, created_to: datetime
    ) -> dict[int, int]:
        query = (
            select(ConsultationRequestModel.trainer_id, func.count())
            .where(
                ConsultationRequestModel.created_at >= created_from,
                ConsultationRequestModel.created_at < created_to,
            )
            .group_by(ConsultationRequestModel.trainer_id)
        )
        result = await self._session.execute(query)
        return dict(result.all())
