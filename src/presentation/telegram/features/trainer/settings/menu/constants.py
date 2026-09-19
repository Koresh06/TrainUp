from aiogram.fsm.state import State

from src.presentation.telegram.features.trainer.settings.questions.states import (
    TrainerQuestionsSG,
)
from src.presentation.telegram.features.trainer.settings.reminder.states import TrainerReminderSettingsSG
from src.presentation.telegram.features.trainer.settings.schedule.states import (
    TrainerScheduleSG,
)
from src.presentation.telegram.features.trainer.blocking.states import TrainerBlockingSG
from src.presentation.telegram.features.trainer.settings.pricing_rule.states import (
    TrainerPricingRuleSG,
)
from src.presentation.telegram.features.trainer.settings.booking.states import (
    TrainerBookingSettingsSG,
)

TRAINER_SETTINGS_TARGETS: dict[str, State] = {
    "schedule": TrainerScheduleSG.main,
    "blocking": TrainerBlockingSG.select_date,
    "pricing": TrainerPricingRuleSG.main,
    "booking_settings": TrainerBookingSettingsSG.main,
    "questions": TrainerQuestionsSG.main,
    "reminder_settings": TrainerReminderSettingsSG.main
}
