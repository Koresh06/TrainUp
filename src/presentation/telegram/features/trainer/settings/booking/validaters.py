def validate_max_bookings(value: str) -> int:
    value = value.strip()
    if not value.isdigit():
        raise ValueError("Введите число. Например: 1")
    count = int(value)
    if not (1 <= count <= 10):
        raise ValueError("Значение должно быть от 1 до 10")
    return count
