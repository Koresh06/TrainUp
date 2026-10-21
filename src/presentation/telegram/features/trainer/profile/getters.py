import logging
from datetime import timedelta
from html import escape

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.get_views import GetBookingViewsRequest
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionRequest,
)
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.booking import BookingStatus
from src.domain.enums.subscription import SubscriptionSource
from src.domain.repositories.booking import BookingView
from src.domain.utils import get_project_today
from src.presentation.telegram.build_media import build_media_attachment
from src.utils.timezone import to_moscow

logger = logging.getLogger(__name__)


def social_links_block(trainer: Trainer) -> str:
    if not trainer.social_links:
        return "—"
    return "\n".join(
        f'<a href="{escape(url)}">{escape(name)}</a>' for name, url in trainer.social_links.items()
    )


async def notification_chat_label(bot: Bot, chat_id: int) -> str:
    """Название рабочей группы — заодно проверка, что бот всё ещё может туда писать."""
    try:
        chat = await bot.get_chat(chat_id)
    except TelegramAPIError as error:
        logger.warning("[TrainerProfile] notification chat %s unavailable: %s", chat_id, error)
        return "⚠️ нет доступа — уведомления не доходят, выберите группу заново"
    title = getattr(chat, "title", None)
    return f"«{escape(title)}»" if title else "подключена"


async def _trainer(dialog_manager: DialogManager, mediator: Mediator) -> Trainer:
    return await mediator.handle(
        GetTrainerByIdRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )


@inject
async def trainer_profile_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer = await _trainer(dialog_manager, mediator)
    clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer.id)
    )
    subscription: TrainerSubscription | None = await mediator.handle(
        GetActiveSubscriptionRequest(trainer_id=trainer.id)
    )
    today = get_project_today()
    completed: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(
            trainer_id=trainer.id,
            date_from=today - timedelta(days=30),
            date_to=today,
            statuses=(BookingStatus.COMPLETED,),
        )
    )
    ratings = [v.booking.rating for v in completed if v.booking.rating is not None]

    if subscription is None:
        subscription_line = "нет активной подписки"
    else:
        until = to_moscow(subscription.expired_at).strftime("%d.%m.%Y")
        subscription_line = (
            f"пробный период до {until}"
            if subscription.source == SubscriptionSource.TRIAL
            else f"до {until}"
        )
    stats = f"👥 Клиентов: {len(clients)} · 🏁 за 30 дней: {len(completed)}"
    if ratings:
        stats += f" · ⭐ {sum(ratings) / len(ratings):.1f}"

    bot: Bot = dialog_manager.middleware_data["bot"]
    return {
        "photo": build_media_attachment(trainer.photo_file_id),
        "name": escape(trainer.name),
        "bio": escape(trainer.bio) if trainer.bio else "—",
        "phone": escape(trainer.phone) if trainer.phone else "—",
        "social_links": social_links_block(trainer),
        "group": await notification_chat_label(bot, trainer.notification_chat_id),
        "subscription": subscription_line,
        "stats": stats,
        "has_photo": trainer.photo_file_id is not None,
        "has_bio": bool(trainer.bio),
        "has_links": bool(trainer.social_links),
    }


@inject
async def client_preview_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    """Ровно то, что клиент видит в «👤 Ваш инструктор»."""
    trainer = await _trainer(dialog_manager, mediator)
    links = (
        "\n\n" + "\n".join(
            f'🔗 <a href="{escape(url)}">{escape(name)}</a>'
            for name, url in trainer.social_links.items()
        )
        if trainer.social_links
        else ""
    )
    return {
        "photo": build_media_attachment(trainer.photo_file_id),
        "name": escape(trainer.name),
        "bio": escape(trainer.bio),
        "links": links,
    }


@inject
async def edit_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer = await _trainer(dialog_manager, mediator)
    return {
        "name": escape(trainer.name),
        "bio": escape(trainer.bio) if trainer.bio else "—",
        "phone": escape(trainer.phone) if trainer.phone else "—",
        "social_links": social_links_block(trainer),
        "photo": build_media_attachment(trainer.photo_file_id),
        "has_photo": trainer.photo_file_id is not None,
        "has_bio": bool(trainer.bio),
        "has_links": bool(trainer.social_links),
    }
