from enum import Enum


class ClientSource(str, Enum):
    # клиент сам зарегистрировался в боте по ссылке тренера
    TELEGRAM = "telegram"
    # тренер завёл карточку вручную — у клиента может не быть Telegram
    MANUAL = "manual"


class ClientEditableField(str, Enum):
    """Поля карточки клиента, которые тренер может менять сам."""

    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    PHONE = "phone"
    TRAINER_NOTE = "trainer_note"
