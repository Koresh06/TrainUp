from aiogram_dialog.api.entities import stack

from src.presentation.telegram.dialog_ids import patch_dialog_intent_ids


def test_intent_ids_do_not_collide_within_one_second() -> None:
    patch_dialog_intent_ids()
    ids = {stack.new_id() for _ in range(200)}
    # без патча 200 id за одну секунду гарантированно дают коллизии (вариантов 100)
    assert len(ids) >= 195
    assert max(len(i) for i in ids) <= 7
