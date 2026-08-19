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


def validate_phone_number(value: str) -> str:
    value = value.strip().replace(" ", "")
    pattern = r"^(?:\+7\d{10}|89\d{9}|\+375\d{9}|80\d{9})$"
    if not re.fullmatch(pattern, value):
        raise ValueError(
            "Некорректный номер телефона.\n"
            "Пример (РФ): <code>+79991234567</code> или <code>89001234567</code>\n"
            "Пример (РБ): <code>+375291234567</code> или <code>80291234567</code>"
        )
    return value


def validate_age(value: str) -> int:
    value = value.strip()
    if not value.isdigit():
        raise ValueError("Возраст должен быть числом. Например: 25")
    age = int(value)
    if not (10 <= age <= 100):
        raise ValueError("Введите реальный возраст (от 10 до 100 лет)")
    return age


def bounded_text(max_length: int = 250):
    def _factory(text: str) -> str:
        text = text.strip()
        if not text:
            raise ValueError("Текст не может быть пустым")
        if len(text) > max_length:
            raise ValueError(f"Слишком длинно, максимум {max_length} символов")
        return text

    return _factory
