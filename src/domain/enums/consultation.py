from enum import Enum


class ConsultationType(str, Enum):
    FREE = "free"
    PAID = "paid"