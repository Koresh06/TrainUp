from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const, Format

from .states import TrainerStatsSG
from .getters import stats_getter
from .handlers import on_period_selected
from .helper import period_row

trainer_stats_dialog = Dialog(
    Window(
        Format(
            "📊 <b>Статистика</b>\n\n"
            "👥 Всего клиентов: {total_clients}\n"
            "🔁 Постоянных клиентов: {recurring_clients}\n"
            "📅 Предстоящих тренировок: {upcoming_bookings}\n"
            "✅ Завершено тренировок: {completed_trainings}\n"
            "❌ Отменено: {cancelled_bookings}"
        ),
        period_row(on_period_selected),
        Cancel(Const("⬅️ Назад")),
        state=TrainerStatsSG.main,
        getter=stats_getter,
    ),
)
