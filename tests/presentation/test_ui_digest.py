"""Настройки сводки в кабинете и кнопка «📅 Открыть расписание» из сводки."""

import re
from datetime import datetime

from aiogram.types import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.application.use_cases.trainer_reminder_settings.get_by_trainer_id import (
    GetTrainerReminderSettingsRequest,
)
from src.infrastructure.notifications.callback_data.digest import TrainerDigestCD
from tests.presentation.conftest import TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription


async def test_digest_settings(ui, run, trainer_setup) -> None:
    trainer_id = trainer_setup["trainer"].id
    await activate_subscription(run, trainer_id)
    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "⚙️ Настройки")
    text = await ui.click(TRAINER_TG, "🔔 Напоминания")
    assert "в 08:00" in text and "выключена" in text

    await ui.click(TRAINER_TG, "🌙 Вечерняя сводка")
    assert "в 20:00" in await ui.click(TRAINER_TG, "20:00")
    await ui.click(TRAINER_TG, "☀️ Утренняя сводка")
    await ui.click(TRAINER_TG, "🔕 Выключить")
    await ui.click(TRAINER_TG, "❌ Присылать в дни без тренировок")
    assert "✅ Присылать в дни без тренировок" in ui.buttons

    settings = await run(GetTrainerReminderSettingsRequest(trainer_id=trainer_id))
    assert (settings.morning_digest_hour, settings.evening_digest_hour) == (None, 20)
    assert settings.digest_on_empty_days


async def test_digest_button_opens_schedule_day(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    day = trainer_setup["tomorrow"]
    message = Message(
        message_id=1, date=datetime.now(), chat=Chat(id=TRAINER_TG, type="private"), text="сводка",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
            text="📅 Открыть расписание", callback_data=TrainerDigestCD(day=day.isoformat()).pack(),
        )]]),
    )
    from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator

    await ui.client(TRAINER_TG).click(message, InlineButtonTextLocator(re.escape("📅 Открыть расписание")))
    assert "Завтра" in ui.text
    assert "Кабинет тренера" in await ui.click(TRAINER_TG, "⬅️ В кабинет")
