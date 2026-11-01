from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.bot_admin import BotAdmin
from src.domain.exception.admin import AdminNotFoundException
from src.domain.repositories.bot_admin import BotAdminRepository
from src.infrastructure.database.models import BotAdminModel


class SQLAlchemyBotAdminRepo(BotAdminRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[BotAdmin]:
        result = await self._session.execute(
            select(BotAdminModel).order_by(BotAdminModel.id)
        )
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_tg_id(self, tg_id: int) -> BotAdmin | None:
        result = await self._session.execute(
            select(BotAdminModel).where(BotAdminModel.tg_id == tg_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, admin: BotAdmin) -> BotAdmin:
        if admin.id == 0:
            model = BotAdminModel.from_entity(admin)
            self._session.add(model)
        else:
            result = await self._session.execute(
                select(BotAdminModel).where(BotAdminModel.id == admin.id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise AdminNotFoundException(tg_id=admin.tg_id)
            model.update_model(admin)

        await self._session.flush()
        return model.to_entity()

    async def delete(self, tg_id: int) -> None:
        await self._session.execute(
            delete(BotAdminModel).where(BotAdminModel.tg_id == tg_id)
        )
