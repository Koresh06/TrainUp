def validate_trainer_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Имя не может быть пустым")
    if len(value) > 255:
        raise ValueError("Слишком длинное имя, максимум 255 символов")
    return value


def validate_trainer_bio(value: str) -> str:
    value = value.strip()
    if len(value) > 255:
        raise ValueError("Слишком длинное описание, максимум 255 символов")
    return value