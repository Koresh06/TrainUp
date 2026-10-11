from src.domain.constants import OTHER_OPTION_LABEL
from src.domain.enums.question_type import QuestionType

OTHER_ANSWER_PREFIX = f"{OTHER_OPTION_LABEL}: "


def is_other_option(option: str) -> bool:
    # startswith — чтобы подхватить и старый вариант «Другое (указать самостоятельно)»
    return option.strip().lower().startswith(OTHER_OPTION_LABEL.lower())


def format_other_answer(text: str) -> str:
    return f"{OTHER_ANSWER_PREFIX}{text}"


def _current_question(dialog_data: dict) -> dict | None:
    questions: list[dict] = dialog_data.get("questions", [])
    index: int = dialog_data.get("question_index", 0)
    if index >= len(questions):
        return None
    return questions[index]


def _restore_selected(data: dict) -> None:
    """Восстанавливает выбранные варианты (и текст «Другое») текущего вопроса
    из уже сохранённых ответов — при «Назад» и при обновлении анкеты."""
    data["current_other_text"] = None
    question = _current_question(data)
    if question is None or question["type"] != QuestionType.MULTI_SELECT.value:
        data["current_selected"] = []
        return

    saved_values: list[str] = data.get("answers", {}).get(str(question["id"]), [])
    selected: list[int] = []
    for i, opt in enumerate(question["options"]):
        if is_other_option(opt):
            custom = next(
                (v for v in saved_values if v.startswith(OTHER_ANSWER_PREFIX)), None
            )
            if custom is not None:
                selected.append(i)
                data["current_other_text"] = custom.removeprefix(OTHER_ANSWER_PREFIX)
                continue
        if opt in saved_values:
            selected.append(i)
    data["current_selected"] = selected


def _other_option_selected(data: dict, question: dict) -> bool:
    return any(
        is_other_option(question["options"][i]) for i in data.get("current_selected", [])
    )


def _build_multi_select_answer(data: dict, question: dict) -> list[str]:
    values = []
    for i in data.get("current_selected", []):
        opt = question["options"][i]
        if is_other_option(opt):
            values.append(format_other_answer(data["current_other_text"]))
        else:
            values.append(opt)
    return values
