from datetime import date
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import ChatEvent, DialogManager
from aiogram_dialog.widgets.kbd import Button, ManagedCalendar, Select

from src.application.mediator import Mediator
from src.application.use_cases.vacation.create import CreateVacationRequest
from src.application.use_cases.vacation.manage import DeleteVacationRequest
from src.application.use_cases.vacation.preview import VacationPreviewDTO

from .states import TrainerVacationSG


async def on_from_picked(
    callback: ChatEvent, widget: ManagedCalendar, dialog_manager: DialogManager,
    clicked_date: date, **kwargs,
) -> None:
    dialog_manager.dialog_data["date_from"] = clicked_date.isoformat()
    await dialog_manager.switch_to(TrainerVacationSG.pick_to)


async def on_to_picked(
    callback: ChatEvent, widget: ManagedCalendar, dialog_manager: DialogManager,
    clicked_date: date, **kwargs,
) -> None:
    if clicked_date < date.fromisoformat(dialog_manager.dialog_data["date_from"]):
        await callback.answer("Последний день не может быть раньше первого", show_alert=True)
        return
    dialog_manager.dialog_data["date_to"] = clicked_date.isoformat()
    await dialog_manager.switch_to(TrainerVacationSG.preview)


@inject
async def on_vacation_confirm(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    result: VacationPreviewDTO = await mediator.handle(
        CreateVacationRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            date_from=date.fromisoformat(dialog_manager.dialog_data["date_from"]),
            date_to=date.fromisoformat(dialog_manager.dialog_data["date_to"]),
        )
    )
    text = (
        f"✅ Период закрыт.\n\n🔒 Слотов закрыто: {result.slots_to_block}\n"
        f"❌ Записей отменено: {len(result.bookings)}"
    )
    if result.offline_clients:
        text += "\n📵 Не забудьте предупредить: " + ", ".join(
            escape(n) for n in result.offline_clients
        )
    dialog_manager.dialog_data["done_text"] = text
    await dialog_manager.switch_to(TrainerVacationSG.done)


async def on_vacation_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data["vacation_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerVacationSG.detail)


@inject
async def on_vacation_delete(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    opened: int = await mediator.handle(
        DeleteVacationRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            vacation_id=dialog_manager.dialog_data["vacation_id"],
        )
    )
    await callback.answer(f"Период удалён, открыто слотов: {opened}", show_alert=True)
    await dialog_manager.switch_to(TrainerVacationSG.list)
