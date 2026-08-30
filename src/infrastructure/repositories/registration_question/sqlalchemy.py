from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.repositories.registration_question import RegistrationQuestionRepository
from src.domain.exception.registration_question import RegistrationQuestionNotFoundException
from src.infrastructure.database.models.registration_question import RegistrationQuestionModel


class SQLAlchemyRegistrationQuestionRepo(RegistrationQuestionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, question_id: int) -> RegistrationQuestion | None:
        model = await self._session.get(RegistrationQuestionModel, question_id)
        return model.to_entity() if model else None

    async def get_active_by_trainer_id(self, trainer_id: int) -> list[RegistrationQuestion]:
        stmt = (
            select(RegistrationQuestionModel)
            .where(
                RegistrationQuestionModel.trainer_id == trainer_id,
                RegistrationQuestionModel.is_active.is_(True),
            )
            .order_by(RegistrationQuestionModel.order)
        )
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_all_by_trainer_id(self, trainer_id: int) -> list[RegistrationQuestion]:
        stmt = (
            select(RegistrationQuestionModel)
            .where(RegistrationQuestionModel.trainer_id == trainer_id)
            .order_by(RegistrationQuestionModel.order)
        )
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def get_by_trainer_and_system_key(
        self, trainer_id: int, system_key: str
    ) -> RegistrationQuestion | None:
        stmt = select(RegistrationQuestionModel).where(
            RegistrationQuestionModel.trainer_id == trainer_id,
            RegistrationQuestionModel.system_key == system_key,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def save(self, question: RegistrationQuestion) -> RegistrationQuestion:
        if question.id == 0:
            model = RegistrationQuestionModel.from_entity(question)
            self._session.add(model)
        else:
            model = await self._session.get(RegistrationQuestionModel, question.id)
            if model is None:
                raise RegistrationQuestionNotFoundException(question.id)
            model.update_model(question)

        await self._session.flush()
        return model.to_entity()

    async def delete(self, question_id: int) -> None:
        model = await self._session.get(RegistrationQuestionModel, question_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()