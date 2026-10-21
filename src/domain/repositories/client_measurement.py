from typing import Protocol

from src.domain.entities.client_measurement import ClientMeasurement


class ClientMeasurementRepository(Protocol):
    async def get_by_client(self, client_id: int) -> list[ClientMeasurement]:
        """Все замеры клиента по дате, старые первыми."""
        ...

    async def save(self, measurement: ClientMeasurement) -> ClientMeasurement: ...

    async def delete(self, measurement_id: int) -> None: ...
