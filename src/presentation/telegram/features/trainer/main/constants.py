from aiogram.fsm.state import State

from src.presentation.telegram.features.trainer.invite_link.states import TrainerInviteLinkSG
from src.presentation.telegram.features.trainer.booking.states import TrainerBookingsSG
from src.presentation.telegram.features.trainer.clients.states import TrainerClientsSG
from src.presentation.telegram.features.trainer.profile.states import TrainerProfileSG
from src.presentation.telegram.features.trainer.recurring.states import TrainerRecurringSG
from src.presentation.telegram.features.trainer.settings.menu.states import TrainerSettingsSG
from src.presentation.telegram.features.trainer.stats.states import TrainerStatsSG


TRAINER_MENU_TARGETS: dict[str, State] = {
    "invite_link": TrainerInviteLinkSG.main,
    "bookings": TrainerBookingsSG.mode,
    "clients": TrainerClientsSG.list,
    "settings": TrainerSettingsSG.main,
    "profile": TrainerProfileSG.main,
    "recurring": TrainerRecurringSG.list,
    "stats": TrainerStatsSG.main
}