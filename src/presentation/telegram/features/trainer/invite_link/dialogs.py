from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const, Format

from .states import TrainerInviteLinkSG
from .getters import invite_link_getter


trainer_invite_link_dialog = Dialog(
    Window(
        Format(
            "🔗 Твоя персональная ссылка для клиентов:\n\n<code>{link_url}</code>\n\n"
            "Отправь её клиентам — по ней они сразу попадут к тебе в бота.",
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerInviteLinkSG.main,
        getter=invite_link_getter,
    )
)
