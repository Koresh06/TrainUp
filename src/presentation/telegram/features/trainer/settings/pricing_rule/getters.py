from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer_pricing_rule.get_by_id import (
    GetTrainerPricingRuleRequest,
)
from src.domain.entities.trainer_pricing_rule import TrainerPricingRule


@inject
async def pricing_rule_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    rule: TrainerPricingRule | None = await mediator.handle(
        GetTrainerPricingRuleRequest(trainer_id=trainer_id)
    )

    if rule is None:
        return {
            "boundary_time": "—",
            "price_before": "—",
            "price_after": "—",
            "trainer_fee": "не указана",
        }

    return {
        "boundary_time": rule.boundary_time.strftime("%H:%M"),
        "price_before": f"{rule.price_before:.0f} BYN",
        "price_after": f"{rule.price_after:.0f} BYN",
        "trainer_fee": (
            f"{rule.trainer_fee:.0f} BYN"
            if rule.trainer_fee is not None
            else "не указана"
        ),
    }
