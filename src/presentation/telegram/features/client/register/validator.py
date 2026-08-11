import re


def validate_phone_number(value: str) -> str:
    value = value.strip().replace(" ", "")
    pattern = r"^(?:\+7|8)\d{10}$"
    if not re.fullmatch(pattern, value):
        raise ValueError(
            "Некорректный номер телефона. Пример: <code>+79991234567</code> или <code>89001234567</code>"
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



