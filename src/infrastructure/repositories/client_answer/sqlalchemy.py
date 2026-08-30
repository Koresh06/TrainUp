from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.client_answer import ClientAnswer
from src.domain.repositories.client_answer import ClientAnswerRepository
from src.domain.exception.client_answer import ClientAnswerNotFoundException
from src.infrastructure.database.models.client_answer import ClientAnswerModel


class SQLAlchemyClientAnswerRepo(ClientAnswerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_client_id(self, client_id: int) -> list[ClientAnswer]:
        stmt = select(ClientAnswerModel).where(ClientAnswerModel.client_id == client_id)
        result = await self._session.execute(stmt)
        return [m.to_entity() for m in result.scalars().all()]

    async def save(self, answer: ClientAnswer) -> ClientAnswer:
        if answer.id == 0:
            model = ClientAnswerModel.from_entity(answer)
            self._session.add(model)
        else:
            model = await self._session.get(ClientAnswerModel, answer.id)
            if model is None:
                raise ClientAnswerNotFoundException(answer.id)
            model.update_model(answer)

        await self._session.flush()
        return model.to_entity()

    async def save_many(self, answers: list[ClientAnswer]) -> list[ClientAnswer]:
        saved: list[ClientAnswer] = []
        for answer in answers:
            saved.append(await self.save(answer))
        return saved
