from aiogram.fsm.state import State

from src.presentation.telegram.features.trainer.invite_link.states import TrainerInviteLinkSG
from src.presentation.telegram.features.trainer.schedule.states import TrainerScheduleSG
from src.presentation.telegram.features.trainer.blocking.states import TrainerBlockingSG
from src.presentation.telegram.features.trainer.booking.states import TrainerBookingsSG
from src.presentation.telegram.features.trainer.client.states import TrainerClientsSG


TRAINER_MENU_TARGETS: dict[str, State] = {
    "invite_link": TrainerInviteLinkSG.main,
    "schedule": TrainerScheduleSG.main,
    "blocking": TrainerBlockingSG.select_date,
    "bookings": TrainerBookingsSG.list,
    "clients": TrainerClientsSG.list,
}