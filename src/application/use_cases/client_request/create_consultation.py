import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client_request._shared import (
    ClientRequestDTO,
    _notify_trainer_about_request,
    _to_client_request_dto,
)
from src.domain.entities.consultation import ConsultationRequest
from src.domain.enums.consultation import ConsultationType
from src.domain.enums.request import ClientRequestKind
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateConsultationRequestRequest(UseCaseRequest):
    client_id: int
    trainer_id: int
    consultation_type: ConsultationType
    comment: str | None = None


@dataclass(kw_only=True)
class CreateConsultationRequestUseCase(
    UseCase[CreateConsultationRequestRequest, ClientRequestDTO]
):
    consultation_repo: ConsultationRequestRepository
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(
        self, command: CreateConsultationRequestRequest
    ) -> ClientRequestDTO:
        saved = await self.consultation_repo.save(
            ConsultationRequest(
                client_id=command.client_id,
                trainer_id=command.trainer_id,
                consultation_type=command.consultation_type,
                comment=command.comment,
            )
        )
        await self.transaction_manager.commit()

        request = _to_client_request_dto(ClientRequestKind.CONSULTATION, saved)
        await _notify_trainer_about_request(
            request=request,
            trainer_repo=self.trainer_repo,
            client_repo=self.client_repo,
            notification_service=self.notification_service,
        )

        logger.info("[CreateConsultationRequest:done] request_id=%s", saved.id)
        return request
