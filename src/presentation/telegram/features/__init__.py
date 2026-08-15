from aiogram import Router
from aiogram_dialog import Dialog


from src.presentation.telegram.features.client.register.router import router as start_router
from src.presentation.telegram.features.trainer.main.router import router as trainer_main_router
from src.presentation.telegram.features.client.booking.router import router as trainer_actions_router

from src.presentation.telegram.features.client.register.dialogs import client_register_dialog
from src.presentation.telegram.features.client.menu.dialogs import client_menu_dialog
from src.presentation.telegram.features.client.booking.dialogs import booking_dialog
from src.presentation.telegram.features.trainer.main.dialogs import trainer_main_dialog
from src.presentation.telegram.features.trainer.schedule.dialogs import trainer_schedule_dialog
from src.presentation.telegram.features.trainer.invite_link.dialogs import trainer_invite_link_dialog
from src.presentation.telegram.features.trainer.subscription.dialogs import subscription_dialog, trainer_onboarding_dialog


def get_all_routers() -> list[Router]:
    return [
        start_router,
        trainer_main_router,
        trainer_actions_router,
    ]


def get_all_dialogs() -> list[Dialog]:
    return [
        client_register_dialog,
        client_menu_dialog,
        booking_dialog,
        trainer_main_dialog,
        trainer_schedule_dialog,
        trainer_invite_link_dialog,
        trainer_onboarding_dialog,
        subscription_dialog,
    ]