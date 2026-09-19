from datetime import datetime, time, timezone
from decimal import Decimal, InvalidOperation


def validate_boundary_time(value: str) -> time:
    value = value.strip()
    try:
        parsed = datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise ValueError("Неверный формат. Введите время как ЧЧ:ММ, например 17:00")
    return parsed.replace(tzinfo=timezone.utc)


def validate_price(value: str) -> Decimal:
    value = value.strip().replace(",", ".")
    try:
        price = Decimal(value)
    except InvalidOperation:
        raise ValueError("Введите число. Например: 23 или 23.50")
    if price < 0:
        raise ValueError("Цена не может быть отрицательной")
    if price > Decimal("99999"):
        raise ValueError("Слишком большая цена")
    return price


def validate_trainer_fee(value: str) -> Decimal | None:
    value = value.strip()
    if value == "-":
        return None
    try:
        fee = Decimal(value.replace(",", "."))
    except InvalidOperation:
        raise ValueError("Введите число или «-», чтобы убрать доплату")
    if fee < 0:
        raise ValueError("Доплата не может быть отрицательной")
    return fee