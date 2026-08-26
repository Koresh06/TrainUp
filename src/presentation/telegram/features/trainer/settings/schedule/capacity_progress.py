from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.text import Text
from aiogram_dialog.widgets.common import WhenCondition


class CapacityProgress(Text):
    def __init__(
        self,
        field: str,
        max_value: int,
        filled: str = "🟩",
        empty: str = "⬜",
        when: WhenCondition = None,
    ):
        super().__init__(when)
        self.field = field
        self.max_value = max_value
        self.filled = filled
        self.empty = empty

    async def _render_text(
        self, data: dict, manager: DialogManager,
    ) -> str:
        if manager.is_preview():
            value = 2
        else:
            value = data.get(self.field, 0)

        done = min(self.max_value, max(0, value))
        rest = self.max_value - done

        return self.filled * done + self.empty * rest