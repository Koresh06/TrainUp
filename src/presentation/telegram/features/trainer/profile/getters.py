from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.application.mediator import Mediator
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionRequest,
)
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.presentation.telegram.build_media import build_media_attachment
from src.utils.timezone import to_moscow


@inject
async def trainer_profile_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    trainer: Trainer = await mediator.handle(
        GetTrainerByIdRequest(trainer_id=trainer_id)
    )
    clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer_id)
    )
    subscription: TrainerSubscription | None = await mediator.handle(
        GetActiveSubscriptionRequest(trainer_id=trainer_id)
    )

    subscription_end_date = (
        to_moscow(subscription.expired_at).strftime("%d.%m.%Y")
        if subscription
        else "нет активной подписки"
    )

    social_links_summary = (
        "\n".join(f"{k}: {v}" for k, v in trainer.social_links.items())
        if trainer.social_links
        else "—"
    )

    return {
        "photo": build_media_attachment(trainer.photo_file_id),
        "clients_count": len(clients),
        "subscription_end_date": subscription_end_date,
        "social_links_summary": social_links_summary,
    }
