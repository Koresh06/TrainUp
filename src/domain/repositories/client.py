from typing import Protocol

from src.domain.entities.client import Client


class ClientRepository(Protocol):
    async def get_all(self) -> list[Client]:
        ...
        
    async def get_by_id(self, client_id: int) -> Client | None:
        ...

    async def get_by_tg_id(self, tg_id: int) -> Client | None:
        ...

    async def get_by_trainer_id(self, trainer_id: int) -> list[Client]:
        ...

    async def save(self, client: Client) -> Client:
        ...