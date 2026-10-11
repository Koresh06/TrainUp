import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client_request._shared import (
    ClientRequestDTO,
    _notify_trainer_about_request,
    _to_client_request_dto,
)
from src.domain.entities.feedback import FeedbackMessage
from src.domain.enums.request import ClientRequestKind
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateFeedbackRequest(UseCaseRequest):
    client_id: int
    trainer_id: int
    # ровно одно из двух: phone — просьба перезвонить, message — сообщение тренеру
    phone: str | None = None
    message: str | None = None


@dataclass(kw_only=True)
class CreateFeedbackUseCase(UseCase[CreateFeedbackRequest, ClientRequestDTO]):
    feedback_repo: FeedbackRepository
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateFeedbackRequest) -> ClientRequestDTO:
        if (command.phone is None) == (command.message is None):
            raise ValueError("Feedback must contain either phone or message")

        saved = await self.feedback_repo.save(
            FeedbackMessage(
                client_id=command.client_id,
                trainer_id=command.trainer_id,
                phone=command.phone,
                message=command.message,
            )
        )
        await self.transaction_manager.commit()

        request = _to_client_request_dto(ClientRequestKind.FEEDBACK, saved)
        await _notify_trainer_about_request(
            request=request,
            trainer_repo=self.trainer_repo,
            client_repo=self.client_repo,
            notification_service=self.notification_service,
        )

        logger.info("[CreateFeedback:done] feedback_id=%s", saved.id)
        return request
