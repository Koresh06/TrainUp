from aiogram_dialog import Window, Dialog
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import SwitchTo, Back, Cancel
from aiogram_dialog.widgets.input import TextInput

from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.features.trainer.settings.booking.states import (
    TrainerBookingSettingsSG,
)

from .getters import booking_settings_getter
from .handlers import (
    on_horizon_entered,
    on_max_bookings_entered,
)
from ..validaters import validate_horizon_days, validate_max_bookings

trainer_booking_settings_dialog = Dialog(
    Window(
        Format(
            "⚙️ <b>Настройки записи</b>\n\n"
            "📅 Горизонт календаря: {horizon_days} дней\n"
            "🔢 Максимум активных записей на клиента: {max_bookings}\n\n"
            "Что изменить?"
        ),
        SwitchTo(
            Const("📅 Горизонт календаря"),
            id="edit_horizon",
            state=TrainerBookingSettingsSG.edit_horizon,
        ),
        SwitchTo(
            Const("🔢 Лимит записей"),
            id="edit_max_bookings",
            state=TrainerBookingSettingsSG.edit_max_bookings,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerBookingSettingsSG.main,
        getter=booking_settings_getter,
    ),
    Window(
        Const("Укажи горизонт календаря в днях (от 1 до 90):"),
        TextInput(
            id="horizon_input",
            type_factory=validate_horizon_days,
            on_success=on_horizon_entered,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerBookingSettingsSG.edit_horizon,
    ),
    Window(
        Const(
            "Сколько активных записей может иметь один клиент одновременно (от 1 до 10):"
        ),
        TextInput(
            id="max_bookings_input",
            type_factory=validate_max_bookings,
            on_success=on_max_bookings_entered,
            on_error=on_input_error,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back",
            state=TrainerBookingSettingsSG.main,
        ),
        state=TrainerBookingSettingsSG.edit_max_bookings,
    ),
)
