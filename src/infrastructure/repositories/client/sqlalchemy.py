from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.client import Client
from src.domain.exception.client import ClientAlreadyExistsException, ClientNotFoundException
from src.domain.repositories.client import ClientRepository
from src.infrastructure.database.models import ClientModel


class SQLAlchemyClientRepo(ClientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Client]:
        query = select(ClientModel)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_id(self, client_id: int) -> Client | None:
        query = select(ClientModel).where(ClientModel.id == client_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_by_tg_id(self, tg_id: int) -> Client | None:
        query = select(ClientModel).where(ClientModel.tg_id == tg_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_by_trainer_id(self, trainer_id: int) -> list[Client]:
        query = select(ClientModel).where(ClientModel.trainer_id == trainer_id)
        result = await self._session.execute(query)
        return [model.to_entity() for model in result.scalars().all()]

    async def save(self, client: Client) -> Client:
        if client.id == 0:
            model = ClientModel.from_entity(client)
            self._session.add(model)
        else:
            query = select(ClientModel).where(ClientModel.id == client.id)
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise ClientNotFoundException(client_id=client.id)
            model.update_model(client)

        try:
            await self._session.flush()
        except IntegrityError as error:
            await self._session.rollback()
            raise ClientAlreadyExistsException(tg_id=client.tg_id) from error

        return model.to_entity()
