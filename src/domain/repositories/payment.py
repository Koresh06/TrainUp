from typing import Protocol

from src.domain.entities.payment import Payment


class PaymentRepository(Protocol):
    async def get_by_external_id(self, external_id: str) -> Payment | None: ...

    async def get_by_external_id_for_update(self, external_id: str) -> Payment | None:
        """Блокирует строку (SELECT ... FOR UPDATE) до конца транзакции — чтобы
        повтор webhook'а / двойное нажатие админа не подтвердили платёж дважды."""
        ...

    async def get_all(self) -> list[Payment]: ...

    async def save(self, payment: Payment) -> Payment: ...
