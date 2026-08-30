from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.domain.entities.trainer import Trainer
from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.presentation.telegram.build_media import build_media_attachment


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

    social_links_block = ""
    if trainer.social_links:
        links = "\n".join(
            f'🔗 <a href="{url}">{name}</a>'
            for name, url in trainer.social_links.items()
        )
        social_links_block = f"\n\n{links}"

    return {
        "trainer_name": trainer.name,
        "trainer_bio": trainer.bio,
        "social_links_block": social_links_block,
        "photo": build_media_attachment(trainer.photo_file_id),
    }
