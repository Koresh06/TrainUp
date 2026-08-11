from aiogram.enums import ButtonStyle
from aiogram_dialog import DialogManager

from src.presentation.telegram.widgets.dynamic_style import DynamicStyle


def _slot_style(data: dict, manager: DialogManager) -> ButtonStyle | None:
    item = data["item"]
    kind = item.get("kind")
    if kind == "free":
        return ButtonStyle.SUCCESS
    if kind == "locked":
        return ButtonStyle.DANGER
    return None


slot_style = DynamicStyle(_slot_style)