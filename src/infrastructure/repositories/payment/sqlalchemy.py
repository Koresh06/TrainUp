from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.payment import Payment
from src.domain.exception.payment import PaymentNotFoundException
from src.domain.repositories.payment import PaymentRepository
from src.infrastructure.database.models import PaymentModel


class SQLAlchemyPaymentRepo(PaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_external_id(self, external_id: str) -> Payment | None:
        query = select(PaymentModel).where(PaymentModel.external_id == external_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_by_external_id_for_update(self, external_id: str) -> Payment | None:
        query = (
            select(PaymentModel)
            .where(PaymentModel.external_id == external_id)
            .with_for_update()
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_all(self) -> list[Payment]:
        result = await self._session.execute(select(PaymentModel))
        return [model.to_entity() for model in result.scalars().all()]

    async def save(self, payment: Payment) -> Payment:
        if payment.id == 0:
            model = PaymentModel.from_entity(payment)
            self._session.add(model)
        else:
            query = select(PaymentModel).where(PaymentModel.id == payment.id)
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise PaymentNotFoundException(payment.external_id)
            model.update_model(payment)

        await self._session.flush()
        return model.to_entity()
