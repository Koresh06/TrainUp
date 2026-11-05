from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel, Column, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.admin.states import AdminPricesSG
from src.presentation.telegram.features.error_handler import on_input_error

from .getters import admin_price_edit_getter, admin_prices_getter
from .handlers import on_price_entered, on_price_plan_selected, validate_price

admin_prices_dialog = Dialog(
    Window(
        Format("{prices_text}"),
        Column(
            Select(
                Format("✏️ {item[label]}"),
                id="admin_price_plan",
                item_id_getter=lambda item: item["id"],
                items="plans",
                on_click=on_price_plan_selected,
            ),
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminPricesSG.list,
        getter=admin_prices_getter,
    ),
    Window(
        Format(
            "💲 <b>{plan_name}</b>\n"
            "Сейчас: <b>{price}</b>\n\n"
            "✏️ Введите новую цену в долларах, например <code>30</code> "
            "или <code>29.99</code>:"
        ),
        TextInput(
            id="admin_price_input",
            type_factory=validate_price,
            on_success=on_price_entered,
            on_error=on_input_error,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_prices", state=AdminPricesSG.list),
        state=AdminPricesSG.edit,
        getter=admin_price_edit_getter,
    ),
)
