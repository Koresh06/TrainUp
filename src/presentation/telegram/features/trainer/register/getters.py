from aiogram.enums import ContentType
from dishka.integrations.aiogram import inject, FromDishka
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from src.application.mediator import Mediator
from src.application.use_cases.subscription.get_active_price_plans import (
    GetActivePricePlansRequest,
)
from src.application.use_cases.payment._shared import SUBSCRIPTION_PLAN_LABELS, usd
from src.application.use_cases.payment.get_methods import GetPaymentMethodsRequest
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.enums.payment import PaymentMethod
from src.presentation.telegram.build_media import build_media_attachment

PLAN_LABELS = SUBSCRIPTION_PLAN_LABELS


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
                "label": f"{PLAN_LABELS.get(p.plan, p.plan.value)} — {usd(p.price)}",
            }
            for p in plans
        ]
    }


@inject
async def select_method_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    price_plan_id: int = dialog_manager.dialog_data["price_plan_id"]
    plans: list[SubscriptionPricePlan] = await mediator.handle(GetActivePricePlansRequest())
    plan = next(p for p in plans if p.id == price_plan_id)
    methods: list[PaymentMethod] = await mediator.handle(GetPaymentMethodsRequest())
    print(methods)

    return {
        "plan_label": PLAN_LABELS.get(plan.plan, plan.plan.value),
        "price": usd(plan.price),
        "methods": [{"id": m.value, "label": m.label()} for m in methods],
        "no_methods": not methods,
    }


async def payment_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    return {
        "instructions": data.get("payment_instructions", ""),
        "payment_url": data.get("payment_url") or "",
        "has_url": bool(data.get("payment_url")),
        "is_paid": data.get("payment_paid", False),
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