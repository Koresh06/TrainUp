from collections.abc import Callable

from aiogram_dialog.api.internal import StyleWidget

from aiogram.enums import ButtonStyle
from aiogram_dialog import DialogManager


from typing import Callable

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.style import BaseStyle

from aiogram_dialog.widgets.common import WhenCondition



class DynamicStyle(BaseStyle):
    def __init__(
        self,
        style_getter: Callable[[dict, DialogManager], ButtonStyle | None],
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self._style_getter = style_getter

    async def _render_style(self, data: dict, manager: DialogManager) -> ButtonStyle | None:
        return self._style_getter(data, manager)

    async def _render_emoji(self, data: dict, manager: DialogManager) -> str | None:
        return None