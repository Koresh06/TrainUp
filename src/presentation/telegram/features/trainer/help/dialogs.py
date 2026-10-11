from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Cancel, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from .getters import trainer_faq_answer_getter, trainer_faq_list_getter
from .states import TrainerHelpSG


async def on_trainer_faq_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["faq_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerHelpSG.answer)


trainer_help_dialog = Dialog(
    Window(
        Format("❓ <b>Помощь: как пользоваться ботом</b>{empty_hint}"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="trainer_faq_select",
                item_id_getter=lambda item: item["id"],
                items="faq_items",
                on_click=on_trainer_faq_selected,
            ),
            id="trainer_faq_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerHelpSG.list,
        getter=trainer_faq_list_getter,
    ),
    Window(
        Format("❓ <b>{question}</b>\n\n{answer}"),
        SwitchTo(Const("⬅️ К вопросам"), id="back_to_list", state=TrainerHelpSG.list),
        state=TrainerHelpSG.answer,
        getter=trainer_faq_answer_getter,
    ),
)
