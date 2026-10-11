from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Group, Select
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.client.validaters import validate_request_comment
from src.presentation.telegram.features.error_handler import on_input_error

from .getters import consultation_confirm_getter, consultation_types_getter
from .handlers import (
    on_comment_entered,
    on_comment_skip,
    on_consultation_confirm,
    on_consultation_type_selected,
)
from .states import ClientConsultationSG

client_consultation_dialog = Dialog(
    Window(
        Const(
            "💬 <b>Консультация с тренером</b>\n\n"
            "Выберите тип консультации:"
        ),
        Group(
            Select(
                Format("{item[label]}"),
                id="consultation_type_select",
                item_id_getter=lambda item: item["id"],
                items="consultation_types",
                on_click=on_consultation_type_selected,
            ),
            width=2,
        ),
        Cancel(Const("⬅️ Назад")),
        state=ClientConsultationSG.consultation_type,
        getter=consultation_types_getter,
    ),
    Window(
        Const(
            "💬 Коротко опишите, с каким вопросом хотите обратиться, "
            "или пропустите этот шаг."
        ),
        TextInput(
            id="consultation_comment_input",
            type_factory=validate_request_comment,
            on_success=on_comment_entered,
            on_error=on_input_error,
        ),
        Button(Const("Пропустить ➡️"), id="skip_comment", on_click=on_comment_skip),
        Back(Const("⬅️ Назад")),
        state=ClientConsultationSG.comment,
    ),
    Window(
        Format(
            "Проверьте заявку:\n\n"
            "💬 Консультация: {consultation_type}\n"
            "📝 Вопрос: {comment}\n\n"
            "Тренер получит заявку и свяжется с вами."
        ),
        Button(
            Const("✅ Отправить заявку"),
            id="confirm_consultation",
            on_click=on_consultation_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientConsultationSG.confirm,
        getter=consultation_confirm_getter,
    ),
)
