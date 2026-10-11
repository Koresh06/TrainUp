from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.payment import Payment
from src.domain.exception.payment import PaymentNotFoundException
from src.domain.repositories.payment import PaymentRepository


@dataclass(frozen=True, eq=False)
class GetPaymentByExternalIdRequest(UseCaseRequest):
    external_id: str


@dataclass(kw_only=True)
class GetPaymentByExternalIdUseCase(UseCase[GetPaymentByExternalIdRequest, Payment]):
    payment_repo: PaymentRepository

    async def __call__(self, command: GetPaymentByExternalIdRequest) -> Payment:
        payment = await self.payment_repo.get_by_external_id(command.external_id)
        if payment is None:
            raise PaymentNotFoundException(command.external_id)
        return payment
