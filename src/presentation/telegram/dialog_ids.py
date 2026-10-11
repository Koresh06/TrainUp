import secrets
import time

from aiogram_dialog.api.entities import stack


def _new_int_id() -> int:
    return int(time.time()) % 100000000 + secrets.randbelow(10_000) * 100000000


def patch_dialog_intent_ids() -> None:
    """
    aiogram_dialog строит id диалога как «секунда + random(0..99)» — всего 100
    вариантов в секунду. Два диалога, открытые в одну секунду (например, меню +
    запись по кнопке из напоминания), с шансом ~1% получают одинаковый id: контекст
    затирается и пользователь ловит UnknownIntent. Расширяем случайную часть до
    10 000 (id длиннее на 1 символ — лимит callback_data в 64 байта не задевает).
    """
    stack.new_int_id = _new_int_id
