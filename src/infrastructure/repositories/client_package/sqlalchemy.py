from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.client_package import ClientPackage
from src.domain.exception.package import PackageNotFoundException
from src.domain.repositories.client_package import ClientPackageRepository
from src.infrastructure.database.models import ClientPackageModel


class SQLAlchemyClientPackageRepo(ClientPackageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, package_id: int) -> ClientPackage | None:
        model = await self._session.get(ClientPackageModel, package_id)
        return model.to_entity() if model is not None else None

    async def get_by_client(self, client_id: int) -> list[ClientPackage]:
        query = (
            select(ClientPackageModel)
            .where(ClientPackageModel.client_id == client_id)
            .order_by(ClientPackageModel.id.desc())
        )
        result = await self._session.execute(query)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_by_trainer(self, trainer_id: int) -> list[ClientPackage]:
        query = (
            select(ClientPackageModel)
            .where(ClientPackageModel.trainer_id == trainer_id)
            .order_by(ClientPackageModel.id.desc())
        )
        result = await self._session.execute(query)
        return [m.to_entity() for m in result.scalars().all()]

    async def save(self, package: ClientPackage) -> ClientPackage:
        if package.id == 0:
            model = ClientPackageModel.from_entity(package)
            self._session.add(model)
        else:
            model = await self._session.get(ClientPackageModel, package.id)
            if model is None:
                raise PackageNotFoundException(package_id=package.id)
            model.update_model(package)
        await self._session.flush()
        return model.to_entity()
