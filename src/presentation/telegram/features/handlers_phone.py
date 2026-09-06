import re

from dishka.integrations.aiogram_dialog import inject
from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput


def validate_phone_number(value: str) -> str:
    value = value.strip().replace(" ", "")
    pattern = r"^(?:\+375\d{9}|80\d{9})$"
    if not re.fullmatch(pattern, value):
        raise ValueError(
            "Некорректный номер телефона.\n"
            "Пример: <code>+375291234567</code> или <code>80291234567</code>"
        )
    return value


@inject
async def on_phone_received_contact(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    new_phone = message.contact.phone_number
    if not new_phone.startswith("+"):
        new_phone = f"+{new_phone}"
    dialog_manager.dialog_data["phone"] = new_phone
    await dialog_manager.next()


@inject
async def on_phone_input_success(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
) -> None:
    dialog_manager.dialog_data["phone"] = value.strip()
    await dialog_manager.next()
