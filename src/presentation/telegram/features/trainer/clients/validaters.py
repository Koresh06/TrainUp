import re

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
