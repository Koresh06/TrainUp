"""«📅 Расписание» тренера: день, неделя, ожидающие, история, карточка записи."""

from datetime import time

from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.domain.enums.booking import BookingStatus
from src.domain.utils import get_project_today
from tests.factories import make_booking, make_slot
from tests.presentation.conftest import CLIENT_TG, TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription, register_client


async def test_schedule_day_pending_and_history(ui, run, trainer_setup, session) -> None:
    trainer = trainer_setup["trainer"]
    await activate_subscription(run, trainer.id)

    # клиент записался сам на завтра → запись ждёт подтверждения
    await register_client(ui, trainer_setup["token"])
    await ui.click(CLIENT_TG, "📅 Записаться на занятия")
    await ui.click(CLIENT_TG, str(trainer_setup["tomorrow"].day))
    await ui.click(CLIENT_TG, "10:00 (2)")
    await ui.click(CLIENT_TG, "✅ Подтвердить")

    # а сегодня утром у тренера уже была тренировка с клиентом без Telegram
    oleg = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Олег", last_name="Ким"))
    past_slot = await make_slot(session, trainer.id, get_project_today(), time(0, 0))
    past = await make_booking(session, oleg, past_slot, BookingStatus.COMPLETED)

    await ui.send(TRAINER_TG, "/trainer")
    assert "📅 Расписание (⏳1)" in ui.buttons
    day = await ui.click(TRAINER_TG, "📅 Расписание (⏳1)")
    assert "Сегодня" in day and "Олег Ким 📵" in day and "1 тренировка" in day

    # прошедшая тренировка: можно отметить неявку
    await ui.click(TRAINER_TG, "00:00 🏁 Олег К. 📵")
    assert "Проведена" in ui.text and "🔁 Перенести" not in ui.buttons
    assert "Клиент не пришёл" in await ui.click(TRAINER_TG, "🚫 Не пришёл")
    assert (await run(GetBookingByIdRequest(booking_id=past.id))).status == BookingStatus.NO_SHOW
    await ui.click(TRAINER_TG, "⬅️ Назад")

    # завтра: запись клиента ждёт подтверждения — подтверждаем из кабинета
    tomorrow = await ui.click(TRAINER_TG, next(b for b in ui.buttons if b.endswith("▶️")))
    assert "ждёт подтверждения" in tomorrow
    await ui.click(TRAINER_TG, "10:00 ⏳ Пётр П.")
    assert "Подтверждена" in await ui.click(TRAINER_TG, "✅ Подтвердить")

    # отмена — через подтверждение, кто отменил — видно в карточке
    assert "Клиент получит уведомление" in await ui.click(TRAINER_TG, "❌ Отменить")
    await ui.click(TRAINER_TG, "❌ Да, отменить")
    assert "отменено: 1" in ui.text

    await ui.click(TRAINER_TG, "🗓 Неделя")
    assert "Неделя" in ui.text
    await ui.click(TRAINER_TG, "⬅️ К расписанию")

    history = await ui.click(TRAINER_TG, "🕓 История")
    assert "🚫 1" in history
    await ui.click(TRAINER_TG, "🚫 Неявки")
    assert "• 🚫 Неявки •" in ui.buttons
    await ui.click(TRAINER_TG, "⬅️ К расписанию")


async def test_schedule_add_client_to_day(ui, run, trainer_setup) -> None:
    trainer = trainer_setup["trainer"]
    await activate_subscription(run, trainer.id)
    await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Анна"))

    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "📅 Расписание")
    await ui.click(TRAINER_TG, next(b for b in ui.buttons if b.endswith("▶️")))
    await ui.click(TRAINER_TG, "➕ Записать клиента")
    await ui.click(TRAINER_TG, "📵 Анна")
    await ui.click(TRAINER_TG, "10:00 (2)")
    day = await ui.click(TRAINER_TG, "✅ Записать")
    assert "Анна 📵" in day and "1 тренировка" in day

    await ui.click(TRAINER_TG, "10:00 ✅ Анна 📵")
    card = await ui.click(TRAINER_TG, "👤 Карточка клиента")
    assert "Анна" in card and "Ближайшие" in card
    assert "Анна" in await ui.click(TRAINER_TG, "⬅️ Назад")  # обратно в запись


async def test_schedule_pick_date(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "📅 Расписание")
    await ui.click(TRAINER_TG, "📆 Дата")
    day = await ui.click(TRAINER_TG, str(trainer_setup["tomorrow"].day))
    assert "Завтра" in day




async def test_client_confirms_attendance(ui, run, trainer_setup, notifications) -> None:
    import re
    from datetime import datetime

    from aiogram.types import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Message
    from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator

    from src.application.use_cases.booking.confirm import ConfirmBookingRequest
    from src.infrastructure.notifications.callback_data.reminder import (
        ReminderAction,
        ReminderActionCD,
    )

    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])
    await ui.click(CLIENT_TG, "📅 Записаться на занятия")
    await ui.click(CLIENT_TG, str(trainer_setup["tomorrow"].day))
    await ui.click(CLIENT_TG, "10:00 (2)")
    await ui.click(CLIENT_TG, "✅ Подтвердить")
    [new_booking] = notifications.of("notify_new_booking")
    await run(ConfirmBookingRequest(booking_id=new_booking.booking_id))

    message = Message(
        message_id=1, date=datetime.now(), chat=Chat(id=CLIENT_TG, type="private"),
        text="Завтра тренировка — придёте?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
            text="✅ Приду",
            callback_data=ReminderActionCD(
                action=ReminderAction.CONFIRM, booking_id=new_booking.booking_id
            ).pack(),
        )]]),
    )
    await ui.client(CLIENT_TG).click(message, InlineButtonTextLocator(re.escape("✅ Приду")))
    booking = await run(GetBookingByIdRequest(booking_id=new_booking.booking_id))
    assert booking.client_confirmed_at is not None

    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, next(b for b in ui.buttons if b.startswith("📅 Расписание")))
    day = await ui.click(TRAINER_TG, next(b for b in ui.buttons if b.endswith("▶️")))
    assert "Пётр Петров 👍" in day
