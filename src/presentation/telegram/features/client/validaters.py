from src.domain.constants import FEEDBACK_MESSAGE_MAX_LENGTH, REQUEST_COMMENT_MAX_LENGTH


def validate_request_comment(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Введите текст комментария")
    if len(value) > REQUEST_COMMENT_MAX_LENGTH:
        raise ValueError(
            f"Слишком длинный комментарий (макс. {REQUEST_COMMENT_MAX_LENGTH} символов)"
        )
    return value


def validate_feedback_message(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Введите текст сообщения")
    if len(value) > FEEDBACK_MESSAGE_MAX_LENGTH:
        raise ValueError(
            f"Слишком длинное сообщение (макс. {FEEDBACK_MESSAGE_MAX_LENGTH} символов)"
        )
    return value
