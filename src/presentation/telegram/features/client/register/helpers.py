from src.domain.enums.question_type import QuestionType


def _current_question(dialog_data: dict) -> dict | None:
    questions: list[dict] = dialog_data.get("questions", [])
    index: int = dialog_data.get("question_index", 0)
    if index >= len(questions):
        return None
    return questions[index]


def _restore_selected(data: dict) -> None:
    question = _current_question(data)
    if question is None or question["type"] != QuestionType.MULTI_SELECT.value:
        data["current_selected"] = []
        return

    saved_values = data.get("answers", {}).get(str(question["id"]), [])
    data["current_selected"] = [
        i for i, opt in enumerate(question["options"]) if opt in saved_values
    ]