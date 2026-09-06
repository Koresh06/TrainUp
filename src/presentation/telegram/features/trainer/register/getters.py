from aiogram.enums import ContentType
from dishka.integrations.aiogram import inject, FromDishka
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from src.application.mediator import Mediator
from src.application.use_cases.subscription.get_active_price_plans import (
    GetActivePricePlansRequest,
)
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.enums.subscription import SubscriptionPlan
from src.presentation.telegram.build_media import build_media_attachment

PLAN_LABELS: dict[SubscriptionPlan, str] = {
    SubscriptionPlan.ONE_MONTH: "1 месяц",
    SubscriptionPlan.THREE_MONTHS: "3 месяца",
    SubscriptionPlan.SIX_MONTHS: "6 месяцев",
    SubscriptionPlan.TWELVE_MONTHS: "12 месяцев",
}


@inject
async def select_plan_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    plans: list[SubscriptionPricePlan] = await mediator.handle(
        GetActivePricePlansRequest()
    )

    return {
        "plans": [
            {
                "id": str(p.id),
                "label": f"{PLAN_LABELS.get(p.plan, p.plan.value)} — {p.price:.0f} BLR",
            }
            for p in plans
        ]
    }


@inject
async def confirm_plan_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    price_plan_id: int = dialog_manager.dialog_data["price_plan_id"]
    plans: list[SubscriptionPricePlan] = await mediator.handle(
        GetActivePricePlansRequest()
    )
    plan = next(p for p in plans if p.id == price_plan_id)

    return {
        "plan_label": PLAN_LABELS.get(plan.plan, plan.plan.value),
        "price": f"{plan.price:.0f}",
    }


async def getter_media(dialog_manager: DialogManager, **kwargs) -> dict:
    photo_file_id = dialog_manager.dialog_data.get("photo_file_id")
    media = None
    if photo_file_id:
        media = MediaAttachment(
            file_id=MediaId(file_id=photo_file_id),
            type=ContentType.PHOTO,
        )
    dialog_manager.dialog_data["media_file_id"] = (
        media.file_id.file_id if media and media.file_id else None
    )

    return {
        "media": media,
        "file_id": bool(photo_file_id),
    }

@inject
async def onboarding_final_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    title = data.get("group_title") or "группа"
    invite_link = data.get("group_invite_link")

    chat_label = f'<a href="{invite_link}">{title}</a>' if invite_link else title
    photo_file_id = data.get("photo_file_id")

    return {
        "name": dialog_manager.find("name").get_value(),
        "bio": dialog_manager.find("bio").get_value(),
        "phone": data.get("phone"),
        "chat_label": chat_label,
        "photo": build_media_attachment(photo_file_id),
    }