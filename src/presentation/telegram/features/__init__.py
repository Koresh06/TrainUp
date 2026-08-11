from aiogram import Router
from aiogram_dialog import Dialog


from src.presentation.telegram.features.client.register.router import router as start_router

from src.presentation.telegram.features.client.register.dialogs import client_register_dialog
from src.presentation.telegram.features.client.menu.dialogs import client_menu_dialog
from src.presentation.telegram.features.client.booking.dialogs import booking_dialog


def get_all_routers() -> list[Router]:
    return [
        start_router,
    ]


def get_all_dialogs() -> list[Dialog]:
    return [
        client_register_dialog,
        client_menu_dialog,
        booking_dialog,
    ]