from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.consultation import ConsultationRequest
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
