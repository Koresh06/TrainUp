from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Column, Button
from aiogram_dialog.widgets.text import Const, Format


from .states import TrainerMainSG
from .getters import trainer_main_getter
from .handlers import on_menu_item_click

trainer_main_dialog = Dialog(
    Window(
        Format("🏋 <b>Кабинет тренера</b>{subscription_line}"),
        Column(
            Button(
                Const("🔗 Тренерская ссылка"),
                id="invite_link",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("📋 Бронирования"),
                id="bookings",
                on_click=on_menu_item_click,
            ),
            Button(
                Format("📨 Заявки{new_requests_badge}"),
                id="requests",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("👥 Мои клиенты"),
                id="clients",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("🔁 Постоянные клиенты"),
                id="recurring",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("⚙️ Настройки"),
                id="settings",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("👤 Профиль"),
                id="profile",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("📊 Статистика"),
                id="stats",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("❓ Помощь"),
                id="help",
                on_click=on_menu_item_click,
            ),
        ),
        state=TrainerMainSG.main,
        getter=trainer_main_getter,
    )
)
