from aiogram.fsm.state import State

from src.presentation.telegram.features.trainer.invite_link.states import TrainerInviteLinkSG
from src.presentation.telegram.features.trainer.booking.states import TrainerBookingsSG
from src.presentation.telegram.features.trainer.client.states import TrainerClientsSG
from src.presentation.telegram.features.trainer.settings.menu.states import TrainerSettingsSG


TRAINER_MENU_TARGETS: dict[str, State] = {
    "invite_link": TrainerInviteLinkSG.main,
    "bookings": TrainerBookingsSG.list,
    "clients": TrainerClientsSG.list,
    "settings": TrainerSettingsSG.main,
}