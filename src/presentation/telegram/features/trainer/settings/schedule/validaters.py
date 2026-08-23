def validate_capacity(value: str) -> int:
    value = value.strip()
    if not value.isdigit():
        raise ValueError("Введите число. Например: 1")
    capacity = int(value)
    if not (1 <= capacity <= 30):
        raise ValueError("Вместимость должна быть от 1 до 30")
    return capacity
