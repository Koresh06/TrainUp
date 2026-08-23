from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.domain.entities.trainer import Trainer
from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest


@inject
async def trainer_profile_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    trainer: Trainer = await mediator.handle(
        GetTrainerByIdRequest(trainer_id=trainer_id)
    )
    return {"trainer_name": trainer.name, "trainer_bio": trainer.bio}
