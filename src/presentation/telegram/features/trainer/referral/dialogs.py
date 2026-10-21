from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Url
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.text import Const, Format

from .getters import trainer_referral_getter
from .states import TrainerReferralSG

trainer_referral_dialog = Dialog(
    Window(
        Format(
            "🎁 <b>Пригласите коллегу-тренера</b>\n\n"
            "<b>Как это работает</b>\n{steps}{rules}\n\n"
            "Ваша ссылка:\n<code>{link}</code>\n\n"
            "{invited}\n\n"
            "<i>Клиентов приглашайте «🔗 Тренерской ссылкой» — это другая программа: "
            "ваши клиенты сами зовут друзей через «🎁 Пригласить друга», а бонус им "
            "настраивается в ⚙️ Настройки → 📅 Запись.</i>"
        ),
        Url(Const("📤 Поделиться"), Format("{share_url}")),
        Cancel(Const("⬅️ Назад")),
        LinkPreview(is_disabled=True),
        state=TrainerReferralSG.main,
        getter=trainer_referral_getter,
    ),
)
