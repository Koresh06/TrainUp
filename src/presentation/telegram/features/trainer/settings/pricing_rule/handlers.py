from datetime import time
from decimal import Decimal

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import Message
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from src.application.mediator import Mediator
from src.application.use_cases.trainer_pricing_rule.get_by_id import (
    GetTrainerPricingRuleRequest,
)
from src.application.use_cases.trainer_pricing_rule.update import (
    UpdateTrainerPricingRuleRequest,
)
from src.domain.entities.trainer_pricing_rule import TrainerPricingRule

from .states import TrainerPricingRuleSG


async def on_open_edit_boundary(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(TrainerPricingRuleSG.edit_boundary_time)


async def on_open_edit_price_before(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(TrainerPricingRuleSG.edit_price_before)


async def on_open_edit_price_after(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(TrainerPricingRuleSG.edit_price_after)


@inject
async def on_boundary_time_entered(
    message: Message,
    widget: ManagedTextInput[time],
    dialog_manager: DialogManager,
    value: time,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    current: TrainerPricingRule = await mediator.handle(
        GetTrainerPricingRuleRequest(trainer_id=trainer_id)
    )

    await mediator.handle(
        UpdateTrainerPricingRuleRequest(
            trainer_id=trainer_id,
            boundary_time=value,
            price_before=current.price_before,
            price_after=current.price_after,
        )
    )
    await message.answer(f"✅ Граница времени обновлена: {value.strftime('%H:%M')}")
    await dialog_manager.switch_to(TrainerPricingRuleSG.main)


@inject
async def on_price_before_entered(
    message: Message,
    widget: ManagedTextInput[Decimal],
    dialog_manager: DialogManager,
    value: Decimal,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    current: TrainerPricingRule = await mediator.handle(
        GetTrainerPricingRuleRequest(trainer_id=trainer_id)
    )

    await mediator.handle(
        UpdateTrainerPricingRuleRequest(
            trainer_id=trainer_id,
            boundary_time=current.boundary_time,
            price_before=value,
            price_after=current.price_after,
        )
    )
    await message.answer(f"✅ Цена до границы обновлена: {value}")
    await dialog_manager.switch_to(TrainerPricingRuleSG.main)


@inject
async def on_price_after_entered(
    message: Message,
    widget: ManagedTextInput[Decimal],
    dialog_manager: DialogManager,
    value: Decimal,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    current: TrainerPricingRule = await mediator.handle(
        GetTrainerPricingRuleRequest(trainer_id=trainer_id)
    )

    await mediator.handle(
        UpdateTrainerPricingRuleRequest(
            trainer_id=trainer_id,
            boundary_time=current.boundary_time,
            price_before=current.price_before,
            price_after=value,
        )
    )
    await message.answer(f"✅ Цена после границы обновлена: {value}")
    await dialog_manager.switch_to(TrainerPricingRuleSG.main)
