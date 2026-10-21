import logging
import uuid
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.interfaces.task_queue import TaskQueue
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.mailing import MailingTarget
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository

logger = logging.getLogger(__name__)

MAILING_BATCH_SIZE = 500


@dataclass(frozen=True, eq=False)
class ExecuteMailingRequest(UseCaseRequest):
    target: MailingTarget
    from_chat_id: int
    message_id: int
    trainer_id: int | None = None


@dataclass(kw_only=True)
class ExecuteMailingUseCase(UseCase[ExecuteMailingRequest, int]):
    """Собирает получателей (без заблокированных, без дублей) и раскладывает
    рассылку на батчи — каждый батч отдельной taskiq-задачей. Возвращает
    число получателей."""

    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    task_queue: TaskQueue

    async def __call__(self, command: ExecuteMailingRequest) -> int:
        try:
            chat_ids = await self._recipients(command)
        except Exception as error:
            logger.exception("[ExecuteMailing] failed to collect recipients")
            await self.notification_service.notify_admins(
                f"❌ Ошибка рассылки ({command.target.label()}):\n<code>{error}</code>"
            )
            return 0

        if not chat_ids:
            await self.notification_service.notify_admins(
                f"ℹ️ Рассылка <b>{command.target.label()}</b>: получателей нет"
            )
            return 0

        batches = [
            chat_ids[i : i + MAILING_BATCH_SIZE]
            for i in range(0, len(chat_ids), MAILING_BATCH_SIZE)
        ]
        mailing_id = uuid.uuid4().hex
        for batch in batches:
            await self.task_queue.enqueue(
                task_name="execute_mailing_batch",
                args=(
                    batch,
                    command.from_chat_id,
                    command.message_id,
                    len(batches),
                    command.target.label(),
                    mailing_id,
                ),
            )

        logger.info(
            "[ExecuteMailing] target=%s recipients=%s batches=%s",
            command.target, len(chat_ids), len(batches),
        )
        return len(chat_ids)

    async def _recipients(self, command: ExecuteMailingRequest) -> list[int]:
        chat_ids: list[int] = []
        if command.target in (MailingTarget.ALL_TRAINERS, MailingTarget.EVERYONE):
            chat_ids += [t.tg_id for t in await self.trainer_repo.get_all() if t.is_active]
        if command.target in (MailingTarget.ALL_CLIENTS, MailingTarget.EVERYONE):
            chat_ids += [
                c.tg_id for c in await self.client_repo.get_all() if c.is_active and c.has_telegram
            ]
        if command.target == MailingTarget.TRAINER_CLIENTS:
            if command.trainer_id is None:
                raise ValueError("trainer_id required")
            clients = await self.client_repo.get_by_trainer_id(command.trainer_id)
            chat_ids += [c.tg_id for c in clients if c.is_active and c.has_telegram]
        return list(dict.fromkeys(chat_ids))  # без дублей, порядок сохраняем
