import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client_request._shared import (
    ClientRequestDTO,
    _notify_trainer_about_request,
    _to_client_request_dto,
)
from src.domain.entities.program import ProgramRequest
from src.domain.enums.program import ProgramType
from src.domain.enums.request import ClientRequestKind
from src.domain.enums.training import TrainingDirection
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.program import ProgramRequestRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateProgramRequestRequest(UseCaseRequest):
    client_id: int
    trainer_id: int
    program_type: ProgramType
    direction: TrainingDirection
    comment: str | None = None


@dataclass(kw_only=True)
class CreateProgramRequestUseCase(UseCase[CreateProgramRequestRequest, ClientRequestDTO]):
    program_repo: ProgramRequestRepository
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateProgramRequestRequest) -> ClientRequestDTO:
        saved = await self.program_repo.save(
            ProgramRequest(
                client_id=command.client_id,
                trainer_id=command.trainer_id,
                program_type=command.program_type,
                direction=command.direction,
                comment=command.comment,
            )
        )
        await self.transaction_manager.commit()

        request = _to_client_request_dto(ClientRequestKind.PROGRAM, saved)
        await _notify_trainer_about_request(
            request=request,
            trainer_repo=self.trainer_repo,
            client_repo=self.client_repo,
            notification_service=self.notification_service,
        )

        logger.info("[CreateProgramRequest:done] request_id=%s", saved.id)
        return request
