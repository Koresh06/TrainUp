from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Cancel, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

from src.presentation.telegram.features.error_handler import on_input_error

from .states import TrainerPricingRuleSG
from .getters import (
    pricing_rule_getter,
)
from .handlers import (
    on_boundary_time_entered,
    on_open_edit_boundary,
    on_open_edit_price_before,
    on_open_edit_price_after,
    on_price_after_entered,
    on_price_before_entered,
)
from .validaters import validate_boundary_time, validate_price

pricing_rule_dialog = Dialog(
    Window(
        Format(
            "💰 <b>Настройки цен</b>\n\n"
            "🕐 Граница времени: {boundary_time}\n"
            "💵 Цена до границы: {price_before}\n"
            "💵 Цена после границы: {price_after}\n\n"
            "Что изменить?"
        ),
        Column(
            Button(
                Const("🕐 Граница времени"),
                id="edit_boundary",
                on_click=on_open_edit_boundary,
            ),
            Button(
                Const("💵 Цена до"),
                id="edit_price_before",
                on_click=on_open_edit_price_before,
            ),
            Button(
                Const("💵 Цена после"),
                id="edit_price_after",
                on_click=on_open_edit_price_after,
            ),
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerPricingRuleSG.main,
        getter=pricing_rule_getter,
    ),
    Window(
        Const("Укажи границу времени в формате ЧЧ:ММ (например, 17:00):"),
        TextInput(
            id="boundary_time_input",
            type_factory=validate_boundary_time,
            on_success=on_boundary_time_entered,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerPricingRuleSG.edit_boundary_time,
    ),
    Window(
        Const("Укажи цену ДО границы времени:"),
        TextInput(
            id="price_before_input",
            type_factory=validate_price,
            on_success=on_price_before_entered,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerPricingRuleSG.edit_price_before,
    ),
    Window(
        Const("Укажи цену ПОСЛЕ границы времени:"),
        TextInput(
            id="price_after_input",
            type_factory=validate_price,
            on_success=on_price_after_entered,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerPricingRuleSG.edit_price_after,
    ),
)
