def validate_option_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Введите текст варианта")
    if len(value) > 255:
        raise ValueError("Слишком длинный текст (макс. 255 символов)")
    return value


def validate_question_label(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Введите текст вопроса")
    if len(value) > 500:
        raise ValueError("Слишком длинный вопрос (макс. 500 символов)")
    return value
