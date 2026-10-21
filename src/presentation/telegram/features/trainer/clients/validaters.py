import re
from decimal import Decimal, InvalidOperation

NAME_MAX_LENGTH = 255
NOTE_MAX_LENGTH = 1000


def validate_client_name(value: str) -> tuple[str, str | None]:
    """«Иван Петров» → ("Иван", "Петров"); фамилия необязательна."""
    parts = value.strip().split(maxsplit=1)
    if not parts:
        raise ValueError("Введите имя клиента")
    if any(len(p) > NAME_MAX_LENGTH for p in parts):
        raise ValueError("Слишком длинное имя")
    return parts[0], (parts[1] if len(parts) > 1 else None)


def validate_any_phone(value: str) -> str:
    # тренер вводит номер со слов клиента — формат любой страны,
    # проверяем только, что это похоже на телефон
    cleaned = re.sub(r"[\s\-()]", "", value.strip())
    if not re.fullmatch(r"\+?\d{7,15}", cleaned):
        raise ValueError("Не похоже на номер телефона. Пример: <code>+375291234567</code>")
    return cleaned


def validate_note(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Заметка пустая")
    if len(value) > NOTE_MAX_LENGTH:
        raise ValueError(f"Не длиннее {NOTE_MAX_LENGTH} символов")
    return value


MAX_PACKAGE_SESSIONS = 100


def validate_sessions(value: str) -> int:
    try:
        n = int(value.strip())
    except ValueError:
        raise ValueError("Введите число занятий, например <code>8</code>") from None
    if not 1 <= n <= MAX_PACKAGE_SESSIONS:
        raise ValueError(f"От 1 до {MAX_PACKAGE_SESSIONS} занятий")
    return n


def validate_price(value: str) -> Decimal:
    try:
        price = Decimal(value.strip().replace(",", ".").replace(" ", ""))
    except InvalidOperation:
        raise ValueError("Введите сумму числом, например <code>250</code>") from None
    if price <= 0 or price > Decimal("1000000"):
        raise ValueError("Сумма должна быть больше нуля")
    return price.quantize(Decimal("0.01"))
