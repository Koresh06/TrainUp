from datetime import date, datetime

from sqlalchemy import Date, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.bot_user import BotUser
from src.domain.repositories.bot_user import BotUserRepository
from src.infrastructure.database.models import BotUserActivityModel, BotUserModel


class SQLAlchemyBotUserRepo(BotUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[BotUser]:
        result = await self._session.execute(select(BotUserModel))
        return [model.to_entity() for model in result.scalars().all()]

    async def get_by_tg_id(self, tg_id: int) -> BotUser | None:
        result = await self._session.execute(
            select(BotUserModel).where(BotUserModel.tg_id == tg_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def touch_activity(
        self,
        *,
        tg_id: int,
        username: str | None,
        first_name: str | None,
        now: datetime,
        activity_date: date,
    ) -> None:
        # ON CONFLICT вместо get+save: первый апдейт нового пользователя часто
        # приходит пачкой (сообщение + callback), и get+save ловил бы unique violation
        stmt = insert(BotUserModel).values(
            tg_id=tg_id,
            username=username,
            first_name=first_name,
            last_activity_at=now,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[BotUserModel.tg_id],
            set_={
                "username": stmt.excluded.username,
                "first_name": stmt.excluded.first_name,
                "last_activity_at": stmt.excluded.last_activity_at,
                "blocked_at": None,
                "updated_at": now,
            },
        )
        await self._session.execute(stmt)
        await self._session.execute(
            insert(BotUserActivityModel)
            .values(tg_id=tg_id, activity_date=activity_date)
            .on_conflict_do_nothing()
        )

    async def set_bot_blocked(self, *, tg_id: int, blocked_at: datetime | None) -> None:
        stmt = insert(BotUserModel).values(tg_id=tg_id, blocked_at=blocked_at)
        stmt = stmt.on_conflict_do_update(
            index_elements=[BotUserModel.tg_id],
            set_={"blocked_at": blocked_at, "updated_at": func.now()},
        )
        await self._session.execute(stmt)

    async def count_active(self, date_from: date, date_to: date) -> int:
        query = select(func.count(func.distinct(BotUserActivityModel.tg_id))).where(
            BotUserActivityModel.activity_date >= date_from,
            BotUserActivityModel.activity_date <= date_to,
        )
        return (await self._session.execute(query)).scalar_one()

    async def count_active_by_bucket(
        self, date_from: date, date_to: date, by_month: bool
    ) -> dict[date, int]:
        bucket = (
            cast(func.date_trunc("month", BotUserActivityModel.activity_date), Date)
            if by_month
            else BotUserActivityModel.activity_date
        )
        query = (
            select(bucket, func.count(func.distinct(BotUserActivityModel.tg_id)))
            .where(
                BotUserActivityModel.activity_date >= date_from,
                BotUserActivityModel.activity_date <= date_to,
            )
            .group_by(bucket)
        )
        result = await self._session.execute(query)
        return {day: count for day, count in result.all()}
