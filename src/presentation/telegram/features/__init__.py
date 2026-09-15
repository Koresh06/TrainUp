from aiogram import Router
from aiogram_dialog import Dialog


from src.presentation.telegram.features.client.register.router import (
    router as start_router,
)
from src.presentation.telegram.features.trainer.main.router import (
    router as trainer_main_router,
)
from src.presentation.telegram.features.trainer.booking.router import (
    router as trainer_actions_router,
)
from src.presentation.telegram.features.client.booking.router import (
    router as client_actions_router,
)

from src.presentation.telegram.features.client.register.dialogs import (
    client_register_dialog,
)
from src.presentation.telegram.features.client.menu.dialogs import client_menu_dialog
from src.presentation.telegram.features.client.booking.dialogs import booking_dialog
from src.presentation.telegram.features.trainer.main.dialogs import trainer_main_dialog
from src.presentation.telegram.features.trainer.settings.schedule.dialogs import (
    trainer_schedule_dialog,
)
from src.presentation.telegram.features.trainer.invite_link.dialogs import (
    trainer_invite_link_dialog,
)
from src.presentation.telegram.features.trainer.register.dialogs import (
    subscription_dialog,
    trainer_onboarding_dialog,
)
from src.presentation.telegram.features.trainer.settings.booking.dialogs import (
    trainer_booking_settings_dialog,
)
from src.presentation.telegram.features.trainer.settings.pricing_rule.dialogs import (
    pricing_rule_dialog,
)
from src.presentation.telegram.features.trainer.settings.menu.dialogs import (
    trainer_settings_dialog,
)
from src.presentation.telegram.features.trainer.profile.dialogs import (
    trainer_profile_dialog,
)
from src.presentation.telegram.features.trainer.settings.questions.dialogs import (
    questions_dialog,
)
from src.presentation.telegram.features.trainer.recurring.dialogs import (
    trainer_recurring_dialog,
)
from src.presentation.telegram.features.trainer.booking.dialogs import (
    list_bookings_dialog,
)
from src.presentation.telegram.features.trainer.stats.dialogs import (
    trainer_stats_dialog,
)
from src.presentation.telegram.features.trainer.clients.dialogs import (
    clients_trainer_dialog,
)


def get_all_routers() -> list[Router]:
    return [
        start_router,
        trainer_main_router,
        trainer_actions_router,
        client_actions_router,
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
        trainer_booking_settings_dialog,
        pricing_rule_dialog,
        trainer_settings_dialog,
        trainer_profile_dialog,
        questions_dialog,
        trainer_recurring_dialog,
        list_bookings_dialog,
        trainer_stats_dialog,
        clients_trainer_dialog,
    ]
