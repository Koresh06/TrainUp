from dataclasses import dataclass
from datetime import datetime

from src.application.interfaces.notification_service import (
    ClientRequestNotificationDTO,
    NotificationService,
)
from src.domain.constants import (
    CONSULTATION_TYPE_LABELS,
    PROGRAM_TYPE_LABELS,
    TRAINING_DIRECTION_LABELS,
)
from src.domain.entities.consultation import ConsultationRequest
from src.domain.entities.feedback import FeedbackMessage
from src.domain.entities.program import ProgramRequest
from src.domain.enums.request import ClientRequestKind, RequestStatus
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository

ClientRequestEntity = ProgramRequest | ConsultationRequest | FeedbackMessage


@dataclass(frozen=True)
class ClientRequestDTO:
    """Единое представление трёх видов заявок для кабинета тренера и уведомлений."""

    kind: ClientRequestKind
    id: int
    client_id: int
    trainer_id: int
    status: RequestStatus
    created_at: datetime
    title: str
    details: str


def _to_client_request_dto(
    kind: ClientRequestKind, request: ClientRequestEntity
) -> ClientRequestDTO:
    if isinstance(request, ProgramRequest):
        title = (
            f"Программа: {PROGRAM_TYPE_LABELS[request.program_type]} · "
            f"{TRAINING_DIRECTION_LABELS[request.direction]}"
        )
        details = request.comment or "Без комментария"
    elif isinstance(request, ConsultationRequest):
        title = f"Консультация: {CONSULTATION_TYPE_LABELS[request.consultation_type]}"
        details = request.comment or "Без комментария"
    elif request.is_callback_request():
        title = "Просьба перезвонить"
        details = f"📞 Перезвонить на номер: {request.phone}"
    else:
        title = "Сообщение тренеру"
        details = request.message or ""

    return ClientRequestDTO(
        kind=kind,
        id=request.id,
        client_id=request.client_id,
        trainer_id=request.trainer_id,
        status=request.status,
        created_at=request.created_at,
        title=title,
        details=details,
    )


async def _notify_trainer_about_request(
    *,
    request: ClientRequestDTO,
    trainer_repo: TrainerRepository,
    client_repo: ClientRepository,
    notification_service: NotificationService,
) -> None:
    trainer = await trainer_repo.get_by_id(request.trainer_id)
    client = await client_repo.get_by_id(request.client_id)
    if trainer is None or client is None:
        return

    full_name = client.first_name
    if client.last_name:
        full_name += f" {client.last_name}"

    await notification_service.notify_client_request(
        ClientRequestNotificationDTO(
            chat_id=trainer.notification_chat_id,
            fallback_chat_id=trainer.tg_id,
            kind=request.kind,
            request_id=request.id,
            title=request.title,
            details=request.details,
            client_full_name=full_name,
            client_tg_id=client.tg_id,
            client_username=client.username,
            client_phone=client.phone,
        )
    )
