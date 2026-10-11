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
from src.presentation.telegram.features.trainer.requests.router import (
    router as trainer_requests_router,
)
from src.presentation.telegram.features.admin.router import router as admin_router
from src.presentation.telegram.features.trainer.register.router import (
    router as trainer_subscription_router,
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
from src.presentation.telegram.features.trainer.settings.reminder.dialogs import (
    trainer_reminder_settings_dialog,
)
from src.presentation.telegram.features.trainer.blocking.dialogs import (
    trainer_blocking_dialog,
)
from src.presentation.telegram.features.trainer.requests.dialogs import (
    trainer_requests_dialog,
)
from src.presentation.telegram.features.client.program.dialogs import (
    client_program_dialog,
)
from src.presentation.telegram.features.client.consultation.dialogs import (
    client_consultation_dialog,
)
from src.presentation.telegram.features.client.feedback.dialogs import (
    client_feedback_dialog,
)
from src.presentation.telegram.features.client.profile.dialogs import (
    client_profile_dialog,
)
from src.presentation.telegram.features.admin.modules.menu.dialogs import admin_menu_dialog
from src.presentation.telegram.features.admin.modules.stats.dialogs import admin_stats_dialog
from src.presentation.telegram.features.admin.modules.trainers.dialogs import (
    admin_trainers_dialog,
)
from src.presentation.telegram.features.admin.modules.clients.dialogs import (
    admin_clients_dialog,
)
from src.presentation.telegram.features.admin.modules.mailing.dialogs import (
    admin_mailing_dialog,
)
from src.presentation.telegram.features.admin.modules.faq.dialogs import admin_faq_dialog
from src.presentation.telegram.features.admin.modules.exports.dialogs import (
    admin_export_dialog,
)
from src.presentation.telegram.features.trainer.help.dialogs import trainer_help_dialog

def get_all_routers() -> list[Router]:
    return [
        start_router,
        trainer_main_router,
        trainer_actions_router,
        client_actions_router,
        trainer_requests_router,
        admin_router,
        trainer_subscription_router,
    ]


# Группы диалогов для guard-middleware (см. presentation/telegram/middlewares):
# кабинет тренера закрывается без подписки, клиентские разделы — если тренер
# недоступен, админка — для всех, кроме ADMIN_IDS.
TRAINER_CABINET_DIALOGS: list[Dialog] = [
    trainer_main_dialog,
    trainer_schedule_dialog,
    trainer_invite_link_dialog,
    trainer_booking_settings_dialog,
    pricing_rule_dialog,
    trainer_settings_dialog,
    trainer_profile_dialog,
    questions_dialog,
    trainer_recurring_dialog,
    list_bookings_dialog,
    trainer_stats_dialog,
    clients_trainer_dialog,
    trainer_reminder_settings_dialog,
    trainer_blocking_dialog,
    trainer_requests_dialog,
]

CLIENT_DIALOGS: list[Dialog] = [
    client_menu_dialog,
    booking_dialog,
    client_program_dialog,
    client_consultation_dialog,
    client_feedback_dialog,
    client_profile_dialog,
]

ADMIN_DIALOGS: list[Dialog] = [
    admin_menu_dialog,
    admin_stats_dialog,
    admin_trainers_dialog,
    admin_clients_dialog,
    admin_mailing_dialog,
    admin_faq_dialog,
    admin_export_dialog,
]

# доступны всегда: регистрация клиента, онбординг/оплата тренера, помощь
OPEN_DIALOGS: list[Dialog] = [
    client_register_dialog,
    trainer_onboarding_dialog,
    subscription_dialog,
    trainer_help_dialog,
]


def get_all_dialogs() -> list[Dialog]:
    return [*OPEN_DIALOGS, *TRAINER_CABINET_DIALOGS, *CLIENT_DIALOGS, *ADMIN_DIALOGS]
