from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Group, Select
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.client.validaters import validate_request_comment
from src.presentation.telegram.features.error_handler import on_input_error

from .getters import (
    comment_getter,
    directions_getter,
    program_confirm_getter,
    program_types_getter,
)
from .handlers import (
    can_skip_comment,
    on_comment_entered,
    on_comment_skip,
    on_direction_selected,
    on_program_confirm,
    on_program_type_selected,
)
from .states import ClientProgramSG

client_program_dialog = Dialog(
    Window(
        Const(
            "🏋 <b>Программа тренировок</b>\n\n"
            "Выберите формат занятий — тренер подберёт программу под вас:"
        ),
        Group(
            Select(
                Format("{item[label]}"),
                id="program_type_select",
                item_id_getter=lambda item: item["id"],
                items="program_types",
                on_click=on_program_type_selected,
            ),
            width=1,
        ),
        Cancel(Const("⬅️ Назад")),
        state=ClientProgramSG.program_type,
        getter=program_types_getter,
    ),
    Window(
        Const("🎯 <b>Выберите направление:</b>"),
        Group(
            Select(
                Format("{item[label]}"),
                id="direction_select",
                item_id_getter=lambda item: item["id"],
                items="directions",
                on_click=on_direction_selected,
            ),
            width=2,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientProgramSG.direction,
        getter=directions_getter,
    ),
    Window(
        Format("💬 {comment_hint}"),
        TextInput(
            id="program_comment_input",
            type_factory=validate_request_comment,
            on_success=on_comment_entered,
            on_error=on_input_error,
        ),
        Button(
            Const("Пропустить ➡️"),
            id="skip_comment",
            on_click=on_comment_skip,
            when=can_skip_comment,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientProgramSG.comment,
        getter=comment_getter,
    ),
    Window(
        Format(
            "✅ <b>Проверьте заявку</b>\n\n"
            "📦 Формат: <b>{program_type}</b>\n"
            "🎯 Направление: <b>{direction}</b>\n"
            "💬 Комментарий: {comment}\n\n"
            "<i>Детали и оплату тренер обсудит с вами лично.</i>"
        ),
        Button(
            Const("📨 Отправить заявку"),
            id="confirm_program",
            on_click=on_program_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientProgramSG.confirm,
        getter=program_confirm_getter,
    ),
)
