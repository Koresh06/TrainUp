from enum import Enum


class SlotStatus(str, Enum):
    FREE = "free"
    BOOKED = "booked"
    BLOCKED = "blocked"


class SlotSource(str, Enum):
    TEMPLATE = "template"   # сгенерирован автоматически из SlotTemplate
    MANUAL = "manual"       # добавлен тренером вручную через настройки бота
