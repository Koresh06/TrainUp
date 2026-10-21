from typing import Protocol

from src.domain.entities.client_package import ClientPackage


class ClientPackageRepository(Protocol):
    async def get_by_id(self, package_id: int) -> ClientPackage | None: ...

    async def get_by_client(self, client_id: int) -> list[ClientPackage]:
        """Все абонементы клиента, новые первыми."""
        ...

    async def get_by_trainer(self, trainer_id: int) -> list[ClientPackage]: ...

    async def save(self, package: ClientPackage) -> ClientPackage: ...
