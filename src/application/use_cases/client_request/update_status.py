import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client_request._shared import (
    ClientRequestDTO,
    _to_client_request_dto,
)
from src.application.use_cases.client_request.get_by_id import (
    GetClientRequestByIdUseCase,
)
from src.domain.entities.consultation import ConsultationRequest
from src.domain.entities.program import ProgramRequest
from src.domain.enums.request import ClientRequestKind, RequestStatus
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class UpdateClientRequestStatusRequest(UseCaseRequest):
    kind: ClientRequestKind
    request_id: int
    status: RequestStatus


@dataclass(kw_only=True)
class UpdateClientRequestStatusUseCase(
    UseCase[UpdateClientRequestStatusRequest, ClientRequestDTO]
):
    get_request_use_case: GetClientRequestByIdUseCase
    transaction_manager: TransactionManager

    async def __call__(self, command: UpdateClientRequestStatusRequest) -> ClientRequestDTO:
        request = await self.get_request_use_case.get_entity(
            command.kind, command.request_id
        )
        request.status = command.status
        request.touch()

        if isinstance(request, ProgramRequest):
            saved = await self.get_request_use_case.program_repo.save(request)
        elif isinstance(request, ConsultationRequest):
            saved = await self.get_request_use_case.consultation_repo.save(request)
        else:
            saved = await self.get_request_use_case.feedback_repo.save(request)
        await self.transaction_manager.commit()

        logger.info(
            "[UpdateClientRequestStatus:done] kind=%s id=%s status=%s",
            command.kind, command.request_id, command.status,
        )
        return _to_client_request_dto(command.kind, saved)
