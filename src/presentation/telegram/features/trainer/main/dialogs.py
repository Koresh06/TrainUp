from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Group
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format


from .states import TrainerMainSG
from .getters import trainer_main_getter
from .handlers import on_menu_item_click

trainer_main_dialog = Dialog(
    Window(
        Format("🏋 <b>Кабинет тренера</b>{subscription_line}"),
        # Главные рабочие кнопки — всю ширину
        Button(
            Format("📅 Расписание{schedule_badge}"),
            id="bookings",
            on_click=on_menu_item_click,
            style=Style(style=ButtonStyle.PRIMARY),
        ),
        Button(
            Format("📨 Заявки{new_requests_badge}"),
            id="requests",
            on_click=on_menu_item_click,
            style=Style(style=ButtonStyle.PRIMARY),
        ),
        # Клиенты — 2 колонки
        Group(
            Button(Const("👥 Мои клиенты"), id="clients", on_click=on_menu_item_click),
            Button(Const("🔁 Постоянные"), id="recurring", on_click=on_menu_item_click),
            width=2,
        ),
        # Профиль и настройки — 2 колонки
        Group(
            Button(Const("👤 Профиль"), id="profile", on_click=on_menu_item_click),
            Button(Const("⚙️ Настройки"), id="settings", on_click=on_menu_item_click),
            width=2,
        ),
        # Аналитика и финансы — 2 колонки
        Group(
            Button(Const("📊 Статистика"), id="stats", on_click=on_menu_item_click),
            Button(
                Const("💎 Подписка"),
                id="subscription",
                on_click=on_menu_item_click,
                style=Style(style=ButtonStyle.SUCCESS),
            ),
            width=2,
        ),
        # Ссылка и реферал — 2 колонки
        Group(
            Button(Const("🔗 Моя ссылка"), id="invite_link", on_click=on_menu_item_click),
            Button(Const("🎁 Пригласить"), id="trainer_referral", on_click=on_menu_item_click),
            width=2,
        ),
        # Помощь — одна строка
        Button(Const("❓ Помощь"), id="help", on_click=on_menu_item_click),
        state=TrainerMainSG.main,
        getter=trainer_main_getter,
    )
)
