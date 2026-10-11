import logging
from dataclasses import dataclass

from src.application.interfaces.mailing_progress import MailingProgressStore
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class ExecuteMailingBatchRequest(UseCaseRequest):
    chat_ids: list[int]
    from_chat_id: int
    message_id: int
    total_batches: int
    target_label: str
    mailing_id: str


@dataclass(kw_only=True)
class ExecuteMailingBatchUseCase(UseCase[ExecuteMailingBatchRequest, None]):
    """Отправляет батч и копит счётчики; последний батч шлёт админам отчёт."""

    notification_service: NotificationService
    progress_store: MailingProgressStore

    async def __call__(self, command: ExecuteMailingBatchRequest) -> None:
        result = await self.notification_service.broadcast_copy(
            chat_ids=command.chat_ids,
            from_chat_id=command.from_chat_id,
            message_id=command.message_id,
        )
        progress = await self.progress_store.add_batch_result(
            mailing_id=command.mailing_id,
            success=result.success,
            blocked=result.blocked,
            failed=result.failed,
        )
        logger.info(
            "[MailingBatch %s/%s] mailing_id=%s success=%s blocked=%s failed=%s",
            progress.done_batches, command.total_batches, command.mailing_id,
            result.success, result.blocked, result.failed,
        )
        if progress.done_batches < command.total_batches:
            return

        total = progress.success + progress.blocked + progress.failed
        await self.notification_service.notify_admins(
            f"✅ Рассылка <b>{command.target_label}</b> завершена\n\n"
            f"📬 Доставлено: <b>{progress.success}</b>\n"
            f"🚫 Заблокировали бота: <b>{progress.blocked}</b>\n"
            f"❌ Другие ошибки: <b>{progress.failed}</b>\n"
            f"👥 Всего: <b>{total}</b>"
        )
        await self.progress_store.clear(mailing_id=command.mailing_id)
