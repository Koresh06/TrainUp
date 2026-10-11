from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_all import GetAllTrainersRequest
from src.domain.entities.trainer import Trainer
from src.domain.enums.mailing import MailingTarget


def mailing_param(dialog_manager: DialogManager, key: str):
    """Параметры рассылки: выбранные в диалоге или переданные при старте
    (из карточки тренера сразу открывается ввод сообщения)."""
    if key in dialog_manager.dialog_data:
        return dialog_manager.dialog_data[key]
    return (dialog_manager.start_data or {}).get(key)


@inject
async def mailing_trainers_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainers: list[Trainer] = await mediator.handle(GetAllTrainersRequest())
    return {
        "trainers": [
            {"id": str(t.id), "label": t.name} for t in trainers if t.is_active
        ]
    }


async def mailing_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    target = MailingTarget(mailing_param(dialog_manager, "target"))
    trainer_name = mailing_param(dialog_manager, "trainer_name")
    target_label = target.label()
    if target == MailingTarget.TRAINER_CLIENTS and trainer_name:
        target_label += f": {escape(trainer_name)}"
    return {"target_label": target_label}
