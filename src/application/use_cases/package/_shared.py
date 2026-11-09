import logging
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.domain.entities.client_package import ClientPackage
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository

logger = logging.getLogger(__name__)


async def _notify_low_balance(
    package: ClientPackage,
    client_repo: ClientRepository,
    trainer_repo: TrainerRepository,
    notification_service: NotificationService,
) -> None:
    if package.remaining > 1:
        return
    client = await client_repo.get_by_id(package.client_id)
    trainer = await trainer_repo.get_by_id(package.trainer_id)
    if client is None or trainer is None:
        return

    if package.remaining == 1:
        client_text = (
            f"🎫 По абонементу «{escape(package.title)}» осталось <b>1 занятие</b>.\n"
            f"Чтобы не прерывать тренировки, продлите абонемент у тренера {escape(trainer.name)}."
        )
    else:
        client_text = (
            f"🎫 Абонемент «{escape(package.title)}» закончился — все занятия использованы.\n"
            f"Продлите его у тренера {escape(trainer.name)}."
        )
        await notification_service.send(
            chat_id=trainer.notification_chat_id,
            fallback_chat_id=trainer.tg_id,
            text=(
                f"🎫 У клиента <b>{escape(client.full_name)}</b> закончился абонемент "
                f"«{escape(package.title)}». Предложите продление."
            ),
        )
    if client.has_telegram:
        await notification_service.send(chat_id=client.tg_id, text=client_text)
