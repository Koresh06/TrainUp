from aiogram.enums import ButtonStyle
from aiogram.types import CallbackQuery, ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    ScrollingGroup,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.trainer._shared import trainer_application_text
from src.application.use_cases.trainer.get_applications import (
    GetTrainerApplicationsRequest,
)
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.application.use_cases.trainer.review import ReviewTrainerRequest
from src.domain.entities.trainer import Trainer
from src.domain.enums.trainer import TrainerApprovalStatus
from src.domain.exception.trainer import TrainerAlreadyReviewedException
from src.presentation.telegram.features.admin.states import AdminApplicationsSG


@inject
async def applications_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainers: list[Trainer] = await mediator.handle(GetTrainerApplicationsRequest())
    return {
        "applications": [
            {
                "id": str(trainer.id),
                "label": f"{'🚫' if trainer.approval_status == TrainerApprovalStatus.REJECTED else '🕓'} "
                f"{trainer.name}",
            }
            for trainer in trainers
        ],
        "empty_hint": "" if trainers else "\n\nНовых заявок нет.",
    }


@inject
async def application_card_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer: Trainer = await mediator.handle(
        GetTrainerByIdRequest(trainer_id=dialog_manager.dialog_data["trainer_id"])
    )
    referrer = (
        await mediator.handle(GetTrainerByIdRequest(trainer_id=trainer.referred_by_trainer_id))
        if trainer.referred_by_trainer_id is not None
        else None
    )
    is_pending = trainer.approval_status == TrainerApprovalStatus.PENDING
    photo = (
        MediaAttachment(
            file_id=MediaId(file_id=trainer.photo_file_id), type=ContentType.PHOTO
        )
        if trainer.photo_file_id
        else None
    )
    return {
        "card_text": trainer_application_text(trainer, referrer)
        + ("" if is_pending else "\n\n🚫 <b>Заявка отклонена</b>"),
        "is_pending": is_pending,
        "can_approve": not trainer.is_approved,
        "photo": photo,
    }


async def on_application_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["trainer_id"] = int(item_id)
    await dialog_manager.switch_to(AdminApplicationsSG.card)


@inject
async def on_application_decision(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    approve = button.widget_id == "application_approve"
    try:
        await mediator.handle(
            ReviewTrainerRequest(
                trainer_id=dialog_manager.dialog_data["trainer_id"],
                approve=approve,
                reviewed_by_tg_id=callback.from_user.id,
            )
        )
    except TrainerAlreadyReviewedException:
        await callback.answer("Заявка уже обработана", show_alert=True)
    else:
        await callback.answer("✅ Тренер подтверждён" if approve else "❌ Заявка отклонена")
    await dialog_manager.switch_to(AdminApplicationsSG.list)


admin_applications_dialog = Dialog(
    Window(
        Format(
            "🛂 <b>Заявки тренеров</b>\n"
            "🕓 ждёт решения · 🚫 отклонена{empty_hint}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="admin_applications_select",
                item_id_getter=lambda item: item["id"],
                items="applications",
                on_click=on_application_selected,
            ),
            id="admin_applications_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminApplicationsSG.list,
        getter=applications_list_getter,
    ),
    Window(
        DynamicMedia(selector="photo", when="photo"),
        Format("{card_text}"),
        Button(
            Const("✅ Подтвердить"),
            id="application_approve",
            on_click=on_application_decision,
            style=Style(style=ButtonStyle.SUCCESS),
            when="can_approve",
        ),
        Button(
            Const("❌ Отклонить"),
            id="application_reject",
            on_click=on_application_decision,
            style=Style(style=ButtonStyle.DANGER),
            when="is_pending",
        ),
        SwitchTo(Const("⬅️ К списку"), id="back_to_list", state=AdminApplicationsSG.list),
        LinkPreview(is_disabled=True),
        state=AdminApplicationsSG.card,
        getter=application_card_getter,
    ),
)
