from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.faq.add import AddFaqItemRequest
from src.application.use_cases.faq.deactivate import DeactivateFaqItemRequest
from src.presentation.telegram.features.admin.states import AdminFaqSG

from .getters import current_audience


def validate_faq_question(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Введите текст вопроса")
    if len(value) > 255:
        raise ValueError("Слишком длинный вопрос (макс. 255 символов)")
    return value


def validate_faq_answer(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Введите текст ответа")
    if len(value) > 3000:
        raise ValueError("Слишком длинный ответ (макс. 3000 символов)")
    return value


async def on_faq_audience_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["faq_audience"] = button.widget_id
    await dialog_manager.switch_to(AdminFaqSG.list)


async def on_faq_item_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["faq_id"] = int(item_id)
    await dialog_manager.switch_to(AdminFaqSG.detail)


@inject
async def on_faq_delete_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        DeactivateFaqItemRequest(faq_id=dialog_manager.dialog_data["faq_id"])
    )
    await callback.answer("Вопрос удалён из FAQ")
    await dialog_manager.switch_to(AdminFaqSG.list)


async def on_faq_question_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
) -> None:
    dialog_manager.dialog_data["new_question"] = value
    await dialog_manager.switch_to(AdminFaqSG.add_answer)


@inject
async def on_faq_answer_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        AddFaqItemRequest(
            question=dialog_manager.dialog_data["new_question"],
            answer=value,
            audience=current_audience(dialog_manager),
        )
    )
    await message.answer("✅ Вопрос добавлен в FAQ")
    await dialog_manager.switch_to(AdminFaqSG.list)
