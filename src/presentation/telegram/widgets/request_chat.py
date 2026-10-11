from collections.abc import Callable

from aiogram.types import (
    ChatAdministratorRights,
    KeyboardButton,
    KeyboardButtonRequestChat,
)
from aiogram_dialog.api.internal import RawKeyboard, TextWidget
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.kbd.base import Keyboard

# права, которые бот запрашивает в выбранной группе/канале — достаточно
# публиковать сообщения (уведомления о записях и заявках)
_BOT_RIGHTS = ChatAdministratorRights(
    is_anonymous=False,
    can_manage_chat=False,
    can_delete_messages=False,
    can_manage_video_chats=False,
    can_restrict_members=False,
    can_promote_members=False,
    can_change_info=False,
    can_invite_users=True,
    can_post_stories=False,
    can_edit_stories=False,
    can_delete_stories=False,
    can_post_messages=True,
)


class RequestChat(Keyboard):
    """
    Reply-кнопка системного выбора чата (KeyboardButtonRequestChat): Telegram
    сам покажет список групп/каналов, добавит туда бота админом и пришлёт
    message.chat_shared. Надёжнее пересылки сообщения: у обычного участника
    группы forward_origin не раскрывает чат.
    """

    def __init__(
        self,
        text: TextWidget,
        request_id: int,
        chat_is_channel: bool,
        when: str | Callable | None = None,
    ):
        super().__init__(when=when)
        self.text = text
        self.request_id = request_id
        self.chat_is_channel = chat_is_channel

    async def _render_keyboard(
        self,
        data: dict,
        manager: DialogManager,
    ) -> RawKeyboard:
        return [
            [
                KeyboardButton(
                    text=await self.text.render_text(data, manager),
                    request_chat=KeyboardButtonRequestChat(
                        request_id=self.request_id,
                        chat_is_channel=self.chat_is_channel,
                        user_administrator_rights=_BOT_RIGHTS,
                        bot_administrator_rights=_BOT_RIGHTS,
                        request_title=True,
                        request_username=True,
                    ),
                ),
            ],
        ]
