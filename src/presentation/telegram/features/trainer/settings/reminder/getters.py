from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer_reminder_settings.get_by_trainer_id import (
    GetTrainerReminderSettingsRequest,
)
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.constants import (
    EVENING_DIGEST_HOUR_OPTIONS,
    MORNING_DIGEST_HOUR_OPTIONS,
    REMINDER_HOUR_OPTIONS,
)


def _hour_label(hour: int | None) -> str:
    return f"в {hour:02d}:00" if hour is not None else "выключена"


async def _settings(dialog_manager: DialogManager, mediator: Mediator) -> TrainerReminderSettings:
    return await mediator.handle(
        GetTrainerReminderSettingsRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )


@inject
async def reminder_settings_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    settings = await _settings(dialog_manager, mediator)
    return {
        "hours_before": settings.hours_before,
        "morning": _hour_label(settings.morning_digest_hour),
        "evening": _hour_label(settings.evening_digest_hour),
        "empty_days": "✅" if settings.digest_on_empty_days else "❌",
    }


@inject
async def reminder_hours_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    settings = await _settings(dialog_manager, mediator)
    return {
        "hours": [
            {
                "id": str(h),
                "label": f"{'✅ ' if h == settings.hours_before else ''}{h} ч.",
            }
            for h in REMINDER_HOUR_OPTIONS
        ]
    }


def _hour_options(options: list[int], current: int | None) -> list[dict]:
    return [
        {"id": str(h), "label": f"{'✅ ' if h == current else ''}{h:02d}:00"}
        for h in options
    ]


@inject
async def morning_digest_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    settings = await _settings(dialog_manager, mediator)
    return {
        "hours": _hour_options(MORNING_DIGEST_HOUR_OPTIONS, settings.morning_digest_hour),
        "is_on": settings.morning_digest_hour is not None,
    }


@inject
async def evening_digest_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    settings = await _settings(dialog_manager, mediator)
    return {
        "hours": _hour_options(EVENING_DIGEST_HOUR_OPTIONS, settings.evening_digest_hour),
        "is_on": settings.evening_digest_hour is not None,
    }
