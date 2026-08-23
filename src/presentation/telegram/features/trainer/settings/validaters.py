def validate_horizon_days(value: str) -> int:
    value = value.strip()
    if not value.isdigit():
        raise ValueError("Введите число дней. Например: 14")
    days = int(value)
    if not (1 <= days <= 90):
        raise ValueError("Горизонт должен быть от 1 до 90 дней")
    return days


def validate_max_bookings(value: str) -> int:
    value = value.strip()
    if not value.isdigit():
        raise ValueError("Введите число. Например: 1")
    count = int(value)
    if not (1 <= count <= 10):
        raise ValueError("Значение должно быть от 1 до 10")
    return count
