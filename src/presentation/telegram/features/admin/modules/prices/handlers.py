from decimal import Decimal, InvalidOperation

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Select
from dishka.integrations.aiogram_dialog import FromDishka, inject

from src.application.mediator import Mediator
from src.application.use_cases.payment._shared import usd
from src.application.use_cases.subscription.price_plans import UpdatePricePlanPriceRequest
from src.presentation.telegram.features.admin.states import AdminPricesSG

from .getters import plan_name

MAX_PRICE = Decimal("100000")


def validate_price(value: str) -> Decimal:
    # «29,99», «$30», «30 $» — так набирают с телефона
    raw = value.strip().replace(",", ".").replace("$", "").replace(" ", "")
    try:
        price = Decimal(raw)
    except InvalidOperation:
        raise ValueError("Введите цену числом, например 30 или 29.99") from None
    if not price.is_finite() or price <= 0:
        raise ValueError("Цена должна быть больше нуля")
    if price > MAX_PRICE:
        raise ValueError(f"Слишком большая цена (макс. {usd(MAX_PRICE)})")
    if price != price.quantize(Decimal("0.01")):
        raise ValueError("Не больше двух знаков после точки (центы)")
    return price.quantize(Decimal("0.01"))


async def on_price_plan_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["price_plan_id"] = int(item_id)
    await dialog_manager.switch_to(AdminPricesSG.edit)


@inject
async def on_price_entered(
    message: Message,
    widget: ManagedTextInput[Decimal],
    dialog_manager: DialogManager,
    value: Decimal,
    mediator: FromDishka[Mediator],
) -> None:
    plan = await mediator.handle(
        UpdatePricePlanPriceRequest(
            price_plan_id=dialog_manager.dialog_data["price_plan_id"],
            price=value,
            changed_by_tg_id=message.from_user.id,
        )
    )
    await message.answer(f"✅ Новая цена «{plan_name(plan)}»: <b>{usd(plan.price)}</b>")
    await dialog_manager.switch_to(AdminPricesSG.list)
