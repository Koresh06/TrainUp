import re


def validate_full_name(value: str) -> tuple[str, str | None]:
    value = value.strip()
    if not value:
        raise ValueError("Введите имя и фамилию")
    parts = value.split(maxsplit=1)
    first_name, last_name = parts[0], (parts[1] if len(parts) > 1 else None)
    if len(first_name) > 50 or (last_name and len(last_name) > 50):
        raise ValueError("Слишком длинное имя или фамилия")
    return first_name, last_name


def validate_age(value: str) -> int:
    value = value.strip()
    if not value.isdigit():
        raise ValueError("Возраст должен быть числом. Например: 25")
    age = int(value)
    if not (10 <= age <= 100):
        raise ValueError("Введите реальный возраст (от 10 до 100 лет)")
    return age