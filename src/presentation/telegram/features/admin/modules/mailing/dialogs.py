from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Column,
    ScrollingGroup,
    Select,
    SwitchTo,
    Back,
)
from aiogram_dialog.widgets.text import Const, Format

from src.domain.enums.mailing import MailingTarget
from src.presentation.telegram.features.admin.states import AdminMailingSG

from .getters import mailing_confirm_getter, mailing_trainers_getter
from .handlers import (
    on_mailing_confirm,
    on_mailing_message_received,
    on_mailing_target_selected,
    on_mailing_trainer_selected,
)

admin_mailing_dialog = Dialog(
    Window(
        Const("📢 <b>Рассылка</b>\n\nКому отправляем?"),
        Column(
            *(
                Button(
                    Const(target.label()),
                    id=target.value,
                    on_click=on_mailing_target_selected,
                )
                for target in MailingTarget
            )
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminMailingSG.target,
    ),
    Window(
        Const("👨‍🏫 Клиентам какого тренера?"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="mailing_trainer_select",
                item_id_getter=lambda item: item["id"],
                items="trainers",
                on_click=on_mailing_trainer_selected,
            ),
            id="mailing_trainers_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Back(Const("⬅️ Назад")),
        state=AdminMailingSG.select_trainer,
        getter=mailing_trainers_getter,
    ),
    Window(
        Const(
            "📝 Отправьте сообщение для рассылки.\n\n"
            "Текст, фото, видео, документ — любой тип, с форматированием. "
            "После отправки покажу предпросмотр."
        ),
        MessageInput(
            func=on_mailing_message_received,
            content_types=ContentType.ANY,
        ),
        Back(Const("⬅️ Назад")),
        state=AdminMailingSG.compose,
    ),
    Window(
        Format(
            "☝️ Так будет выглядеть рассылка.\n\n"
            "📨 Получатели: <b>{target_label}</b>\n"
            "Заблокированные пользователи не получат сообщение.\n\n"
            "✅ Запустить?"
        ),
        Column(
            Button(
                Const("🚀 Отправить"),
                id="confirm_send",
                on_click=on_mailing_confirm,
            ),
            SwitchTo(
                Const("✏️ Изменить сообщение"),
                id="to_compose",
                state=AdminMailingSG.compose,
            ),
            Cancel(Const("❌ Отменить")),
        ),
        state=AdminMailingSG.confirm,
        getter=mailing_confirm_getter,
    ),
)
