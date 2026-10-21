import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import (
    NotificationService,
    PlanNextTrainingNotificationDTO,
)
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client._shared import get_trainer_client
from src.domain.enums.booking import BookingStatus
from src.domain.exception.client import ClientAccessDeniedException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.utils import get_project_today

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class InviteClientBackRequest(UseCaseRequest):
    trainer_id: int
    client_id: int


@dataclass(kw_only=True)
class InviteClientBackUseCase(UseCase[InviteClientBackRequest, None]):
    """Тренер зовёт пропавшего клиента: то же сообщение «пора записаться» с кнопкой."""

    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    booking_repo: BookingRepository
    notification_service: NotificationService

    async def __call__(self, command: InviteClientBackRequest) -> None:
        client = await get_trainer_client(
            self.client_repo, client_id=command.client_id, trainer_id=command.trainer_id
        )
        if not client.has_telegram:
            raise ClientAccessDeniedException(client_id=client.id, trainer_id=command.trainer_id)
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)

        views = await self.booking_repo.get_views(
            trainer_id=command.trainer_id,
            client_id=client.id,
            statuses=(BookingStatus.COMPLETED,),
            newest_first=True,
            limit=1,
        )
        days = (get_project_today() - views[0].slot_date).days if views else 0
        await self.notification_service.notify_plan_next_training(
            PlanNextTrainingNotificationDTO(
                chat_id=client.tg_id,
                trainer_name=trainer.name if trainer else "",
                days_since_training=days,
            )
        )
        logger.info("[InviteClientBack:done] client_id=%s", client.id)
