from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.client_measurement import ClientMeasurement
from src.domain.repositories.client_measurement import ClientMeasurementRepository
from src.infrastructure.database.models import ClientMeasurementModel


class SQLAlchemyClientMeasurementRepo(ClientMeasurementRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_client(self, client_id: int) -> list[ClientMeasurement]:
        query = (
            select(ClientMeasurementModel)
            .where(ClientMeasurementModel.client_id == client_id)
            .order_by(ClientMeasurementModel.measured_on, ClientMeasurementModel.id)
        )
        result = await self._session.execute(query)
        return [m.to_entity() for m in result.scalars().all()]

    async def save(self, measurement: ClientMeasurement) -> ClientMeasurement:
        model = ClientMeasurementModel.from_entity(measurement)
        self._session.add(model)
        await self._session.flush()
        return model.to_entity()

    async def delete(self, measurement_id: int) -> None:
        await self._session.execute(
            delete(ClientMeasurementModel).where(ClientMeasurementModel.id == measurement_id)
        )
        await self._session.flush()
