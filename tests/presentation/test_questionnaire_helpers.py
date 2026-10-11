from src.presentation.telegram.features.client.register.helpers import (
    _build_multi_select_answer,
    _other_option_selected,
    _restore_selected,
    format_other_answer,
    is_other_option,
)

QUESTION = {
    "id": 7,
    "type": "multi_select",
    "label": "Здоровье",
    "options": ["Полностью здоров(-а)", "Проблемы со спиной", "Другое"],
}


def test_other_option_detection_includes_legacy_label() -> None:
    assert is_other_option("Другое")
    assert is_other_option("Другое (указать самостоятельно)")
    assert not is_other_option("Проблемы со спиной")


def test_build_answer_replaces_other_with_custom_text() -> None:
    data = {"current_selected": [1, 2], "current_other_text": "болит колено"}
    assert _other_option_selected(data, QUESTION)
    assert _build_multi_select_answer(data, QUESTION) == [
        "Проблемы со спиной",
        "Другое: болит колено",
    ]


def test_restore_selected_recovers_custom_text() -> None:
    data = {
        "questions": [QUESTION],
        "question_index": 0,
        "answers": {"7": ["Проблемы со спиной", format_other_answer("болит колено")]},
    }
    _restore_selected(data)
    assert data["current_selected"] == [1, 2]
    assert data["current_other_text"] == "болит колено"


def test_restore_selected_for_text_question_resets_state() -> None:
    data = {
        "questions": [{"id": 1, "type": "text", "label": "?", "options": []}],
        "question_index": 0,
        "answers": {"1": ["ответ"]},
    }
    _restore_selected(data)
    assert data["current_selected"] == [] and data["current_other_text"] is None
