from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import FromDishka, inject

from src.application.mediator import Mediator
from src.application.use_cases.payment._shared import SUBSCRIPTION_PLAN_LABELS, usd
from src.application.use_cases.subscription.price_plans import GetAllPricePlansRequest
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.presentation.telegram.features.trainer.register.texts import (
    monthly_base_price,
    plan_button_label,
)


def plan_name(plan: SubscriptionPricePlan) -> str:
    return SUBSCRIPTION_PLAN_LABELS.get(plan.plan, plan.plan.value)


async def _plans(mediator: Mediator) -> list[SubscriptionPricePlan]:
    return await mediator.handle(GetAllPricePlansRequest())


@inject
async def admin_prices_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    plans = await _plans(mediator)
    base = monthly_base_price([p for p in plans if p.is_active])
    # тренер видит такие же подписи на экране оплаты — сразу понятно,
    # как новая цена меняет «выгоду» длинных тарифов
    lines = "\n".join(
        f"• {plan_button_label(p, base)}{'' if p.is_active else ' (скрыт)'}" for p in plans
    )
    return {
        "prices_text": (
            "💲 <b>Цены подписки</b>\n\n"
            f"{lines or 'Тарифов нет.'}\n\n"
            "Цены в долларах. Для оплаты в Stars и рублях бот пересчитывает их "
            "по курсу из настроек. Новая цена работает для новых оплат, уже "
            "открытые счета остаются со старой суммой.\n\n"
            "Выберите тариф, чтобы изменить цену:"
        ),
        "plans": [
            {"id": str(p.id), "label": f"{plan_name(p)} — {usd(p.price)}"} for p in plans
        ],
    }


@inject
async def admin_price_edit_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    plan_id = dialog_manager.dialog_data["price_plan_id"]
    plan = next(p for p in await _plans(mediator) if p.id == plan_id)
    return {
        "plan_name": plan_name(plan),
        "price": usd(plan.price),
    }
