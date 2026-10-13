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
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionRequest,
)
from src.domain.constants import SUBSCRIPTION_WARNING_HOURS, TRAINER_TRIAL_DAYS
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.payment import PaymentMethod
from src.domain.enums.subscription import SubscriptionSource
from src.presentation.telegram.build_media import build_media_attachment
from src.utils.timezone import to_moscow

from .texts import (
    BENEFITS_SHORT,
    TRIAL_LABEL,
    cheapest_per_day,
    days_word,
    monthly_base_price,
    plan_button_label,
)

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
    subscription: TrainerSubscription | None = await mediator.handle(
        GetActiveSubscriptionRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )
    base_price = monthly_base_price(plans)
    per_day = cheapest_per_day(plans)

    return {
        "status_line": _subscription_status(subscription),
        "benefits": BENEFITS_SHORT,
        "per_day_line": f"💡 Всего от <b>{per_day} в день</b> на длинном тарифе.\n" if per_day else "",
        "plans": [
            {"id": str(p.id), "label": plan_button_label(p, base_price)}
            for p in plans
        ],
    }


def _subscription_status(subscription: TrainerSubscription | None) -> str:
    if subscription is None:
        return (
            "⛔ Подписка не активна — кабинет закрыт, клиенты не могут записаться. "
            "Все данные сохранены и вернутся сразу после оплаты."
        )
    until = to_moscow(subscription.expired_at).strftime("%d.%m.%Y")
    if subscription.source == SubscriptionSource.TRIAL:
        return (
            f"🎁 Сейчас пробный период до <b>{until}</b>. Оформи подписку заранее — "
            f"срок начнётся после пробного, ни один день не пропадёт."
        )
    return f"✅ Подписка активна до <b>{until}</b>."


async def welcome_getter(**kwargs) -> dict:
    return {
        "welcome_step_two": (
            f"2️⃣ Сразу получишь <b>{TRIAL_LABEL} бесплатно</b> — все возможности, "
            f"без оплаты и привязки карты"
            if TRAINER_TRIAL_DAYS
            else "2️⃣ Выберешь тариф и оплатишь подписку"
        ),
    }


@inject
async def trial_started_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    subscription: TrainerSubscription | None = await mediator.handle(
        GetActiveSubscriptionRequest(trainer_id=dialog_manager.dialog_data["trainer_id"])
    )
    warnings = " и ".join(
        f"{h // 24} {days_word(h // 24)}" if h % 24 == 0 else f"{h} ч."
        for h in SUBSCRIPTION_WARNING_HOURS
    )
    # срок — из самой подписки, а не из конфига: экран не соврёт, даже если
    # конфиг поменяли после регистрации
    days = (
        round((subscription.expired_at - subscription.started_at).total_seconds() / 86400)
        if subscription
        else TRAINER_TRIAL_DAYS
    )
    return {
        "warning_line": (
            f"За {warnings} до конца пробного периода напомню, чтобы запись "
            f"клиентов не прервалась."
            if warnings
            else ""
        ),
        "trial_days": f"{days} {days_word(days)}",
        "trial_until": (
            to_moscow(subscription.expired_at).strftime("%d.%m.%Y") if subscription else "—"
        ),
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