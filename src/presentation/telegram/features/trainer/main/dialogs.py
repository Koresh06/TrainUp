from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Column, Button
from aiogram_dialog.widgets.text import Const


from .states import TrainerMainSG
from .handlers import on_menu_item_click

trainer_main_dialog = Dialog(
    Window(
        Const("Кабинет тренера. Что делаем?"),
        Column(
            Button(
                Const("🔗 Тренерская ссылка"),
                id="invite_link",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("🗓 Настройка расписания"),
                id="schedule",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("🚫 Блокировка дней/слотов"),
                id="blocking",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("📋 Бронирования"),
                id="bookings",
                on_click=on_menu_item_click,
            ),
            Button(
                Const("👥 Мои клиенты"),
                id="clients",
                on_click=on_menu_item_click,
            ),
        ),
        state=TrainerMainSG.main,
    )
)
