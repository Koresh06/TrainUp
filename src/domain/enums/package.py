from enum import Enum


class PackageStatus(str, Enum):
    ACTIVE = "active"
    # все занятия списаны
    FINISHED = "finished"
    # тренер закрыл вручную (возврат денег, ошибка)
    CANCELLED = "cancelled"
