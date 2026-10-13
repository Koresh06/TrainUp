from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.client_request._shared import ClientRequestDTO
from src.application.use_cases.client_request.get_by_trainer import (
    GetClientRequestsByTrainerRequest,
)
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionRequest,
)
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionSource
from src.utils.timezone import to_moscow


def subscription_line(subscription: TrainerSubscription | None) -> str:
    if subscription is None:
        return ""
    until = to_moscow(subscription.expired_at).strftime("%d.%m.%Y")
    if subscription.source == SubscriptionSource.TRIAL:
        return f"\n🎁 Пробный период до {until} — тарифы в «💎 Подписка»"
    return f"\n💳 Подписка до {until}"


@inject
async def trainer_main_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    new_requests: list[ClientRequestDTO] = await mediator.handle(
        GetClientRequestsByTrainerRequest(trainer_id=trainer_id)
    )
    subscription: TrainerSubscription | None = await mediator.handle(
        GetActiveSubscriptionRequest(trainer_id=trainer_id)
    )
    return {
        "new_requests_badge": f" ({len(new_requests)} 🆕)" if new_requests else "",
        "subscription_line": subscription_line(subscription),
    }
