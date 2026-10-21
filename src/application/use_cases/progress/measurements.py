import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client_measurement import ClientMeasurement
from src.domain.enums.booking import BookingActor
from src.domain.exception.client import ClientNotFoundException
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_measurement import ClientMeasurementRepository
from src.domain.utils import get_project_today
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class AddMeasurementRequest(UseCaseRequest):
    client_id: int
    added_by: BookingActor
    weight: Decimal | None = None
    waist: Decimal | None = None
    chest: Decimal | None = None
    hips: Decimal | None = None
    photo_file_id: str | None = None
    measured_on: date | None = None


@dataclass(kw_only=True)
class AddMeasurementUseCase(UseCase[AddMeasurementRequest, ClientMeasurement]):
    """Замер в дневник прогресса — вносит тренер или сам клиент."""

    measurement_repo: ClientMeasurementRepository
    client_repo: ClientRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: AddMeasurementRequest) -> ClientMeasurement:
        client = await self.client_repo.get_by_id(command.client_id)
        if client is None:
            raise ClientNotFoundException(client_id=command.client_id)
        measurement = ClientMeasurement(
            trainer_id=client.trainer_id,
            client_id=client.id,
            measured_on=command.measured_on or get_project_today(),
            weight=command.weight,
            waist=command.waist,
            chest=command.chest,
            hips=command.hips,
            photo_file_id=command.photo_file_id,
            added_by=command.added_by,
        )
        if measurement.is_empty:
            raise ValueError("empty measurement")
        saved = await self.measurement_repo.save(measurement)
        await self.transaction_manager.commit()
        logger.info("[AddMeasurement:done] client_id=%s by=%s", client.id, command.added_by)
        return saved


@dataclass(frozen=True, eq=False)
class GetMeasurementsRequest(UseCaseRequest):
    client_id: int


@dataclass(kw_only=True)
class GetMeasurementsUseCase(UseCase[GetMeasurementsRequest, list[ClientMeasurement]]):
    measurement_repo: ClientMeasurementRepository

    async def __call__(self, command: GetMeasurementsRequest) -> list[ClientMeasurement]:
        return await self.measurement_repo.get_by_client(command.client_id)


@dataclass(frozen=True, eq=False)
class DeleteMeasurementRequest(UseCaseRequest):
    client_id: int
    measurement_id: int


@dataclass(kw_only=True)
class DeleteMeasurementUseCase(UseCase[DeleteMeasurementRequest, None]):
    measurement_repo: ClientMeasurementRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: DeleteMeasurementRequest) -> None:
        # удалить можно только замер этого клиента — id приходит из callback
        own = {m.id for m in await self.measurement_repo.get_by_client(command.client_id)}
        if command.measurement_id not in own:
            return
        await self.measurement_repo.delete(command.measurement_id)
        await self.transaction_manager.commit()
