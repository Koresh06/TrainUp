from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.application.use_cases.trainer.set_blocked import SetTrainerBlockedRequest
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.mailing import MailingTarget
from src.domain.enums.subscription import SubscriptionSource
from src.presentation.telegram.features.admin.states import AdminMailingSG, AdminTrainersSG
from src.utils.timezone import to_moscow


@inject
async def on_trainer_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    trainer: Trainer = await mediator.handle(GetTrainerByIdRequest(trainer_id=int(item_id)))
    dialog_manager.dialog_data["trainer_id"] = trainer.id
    dialog_manager.dialog_data["trainer_name"] = trainer.name
    await dialog_manager.switch_to(AdminTrainersSG.card)


async def on_grant_plan_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["grant_plan_id"] = int(item_id)
    dialog_manager.dialog_data["grant_days"] = None
    await dialog_manager.switch_to(AdminTrainersSG.grant_confirm)


async def on_grant_days_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["grant_days"] = int(item_id)
    dialog_manager.dialog_data["grant_plan_id"] = None
    await dialog_manager.switch_to(AdminTrainersSG.grant_confirm)


async def on_grant_days_entered(
    message: Message,
    widget: ManagedTextInput[int],
    dialog_manager: DialogManager,
    value: int,
) -> None:
    dialog_manager.dialog_data["grant_days"] = value
    dialog_manager.dialog_data["grant_plan_id"] = None
    await dialog_manager.switch_to(AdminTrainersSG.grant_confirm)


@inject
async def on_grant_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    data = dialog_manager.dialog_data
    if data.get("grant_plan_id"):
        request = GrantSubscriptionRequest(
            trainer_id=data["trainer_id"],
            source=SubscriptionSource.CASH,
            price_plan_id=data["grant_plan_id"],
        )
    else:
        request = GrantSubscriptionRequest(
            trainer_id=data["trainer_id"],
            source=SubscriptionSource.TRIAL,
            days=data["grant_days"],
        )
    subscription: TrainerSubscription = await mediator.handle(request)
    await callback.answer(
        f"✅ Подписка выдана до {to_moscow(subscription.expired_at).strftime('%d.%m.%Y')}",
        show_alert=True,
    )
    await dialog_manager.switch_to(AdminTrainersSG.card)


@inject
async def on_toggle_block_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer: Trainer = await mediator.handle(
        GetTrainerByIdRequest(trainer_id=dialog_manager.dialog_data["trainer_id"])
    )
    await mediator.handle(
        SetTrainerBlockedRequest(trainer_id=trainer.id, blocked=trainer.is_active)
    )
    await callback.answer("⛔ Заблокирован" if trainer.is_active else "✅ Разблокирован")
    await dialog_manager.switch_to(AdminTrainersSG.card)


async def on_mail_trainer_clients(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(
        state=AdminMailingSG.compose,
        data={
            "target": MailingTarget.TRAINER_CLIENTS.value,
            "trainer_id": dialog_manager.dialog_data["trainer_id"],
            "trainer_name": dialog_manager.dialog_data["trainer_name"],
        },
    )


def validate_grant_days(value: str) -> int:
    value = value.strip()
    if not value.isdigit() or not (1 <= int(value) <= 3650):
        raise ValueError("Введите число дней от 1 до 3650")
    return int(value)
