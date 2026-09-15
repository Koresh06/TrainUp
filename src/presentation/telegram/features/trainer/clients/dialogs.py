from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Select, ScrollingGroup, Back
from aiogram_dialog.widgets.text import Const, Format

from .states import TrainerClientsSG
from .getters import client_detail_getter, clients_list_getter
from .handlers import on_client_item_selected

clients_trainer_dialog = Dialog(
    Window(
        Const("👥 <b>Мои клиенты</b>"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="clients_list_select",
                item_id_getter=lambda item: item["id"],
                items="clients",
                on_click=on_client_item_selected,
            ),
            id="clients_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerClientsSG.list,
        getter=clients_list_getter,
    ),
    Window(
        Format(
            "👤 <b>{full_name}</b>\n\n"
            "📞 {phone}\n"
            "💬 {username}\n"
            "🎂 {age} лет\n"
            "🏋️ Стаж: {sport_experience}\n"
            "{recurring_note}\n\n"
            "{answers_summary}"
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerClientsSG.detail,
        getter=client_detail_getter,
    ),
)
