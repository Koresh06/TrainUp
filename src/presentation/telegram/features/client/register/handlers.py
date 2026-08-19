from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput

from src.application.mediator import Mediator
from src.application.use_cases.client.register import RegisterClientRequest
from src.domain.enums.training import HealthCondition
from src.domain.exception.client import AssigningClientToAnotherTrainerError
from src.presentation.telegram.features.client.menu.states import ClientMenuSG

from .states import ClientRegisterSG


async def on_full_name_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: tuple[str, str | None],
) -> None:
    (
        dialog_manager.dialog_data["first_name"],
        dialog_manager.dialog_data["last_name"],
    ) = data
    await dialog_manager.switch_to(ClientRegisterSG.age)


@inject
async def on_age_input_success(
    message: Message,
    widget: ManagedTextInput[int],
    dialog_manager: DialogManager,
    value: int,
) -> None:
    dialog_manager.dialog_data["age"] = value
    await dialog_manager.next()


@inject
async def on_phone_received_contact(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    new_phone = message.contact.phone_number
    if not new_phone.startswith("+"):
        new_phone = f"+{new_phone}"
    dialog_manager.dialog_data["phone"] = new_phone
    await dialog_manager.next()


@inject
async def on_phone_input_success(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
) -> None:
    dialog_manager.dialog_data["phone"] = value.strip()
    await dialog_manager.next()


async def on_sport_experience_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["sport_experience"] = item_id
    await dialog_manager.next()


async def on_health_conditions_done(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    multiselect = dialog_manager.find("health_conditions_multiselect")
    checked: list[str] = multiselect.get_checked()

    if not checked:
        await callback.answer("Выбери хотя бы один вариант", show_alert=True)
        return

    dialog_manager.dialog_data["health_conditions"] = checked

    if HealthCondition.OTHER.value in checked:
        await dialog_manager.switch_to(ClientRegisterSG.health_conditions_other)
    else:
        await dialog_manager.switch_to(ClientRegisterSG.goals)


async def on_health_conditions_other_entered(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    dialog_manager.dialog_data["health_conditions_other_text"] = data
    await dialog_manager.next()


async def on_goals_done(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    multiselect = dialog_manager.find("goals_multiselect")
    checked: list[str] = multiselect.get_checked()

    if not checked:
        await callback.answer("Выбери хотя бы одну цель", show_alert=True)
        return

    dialog_manager.dialog_data["goals"] = checked
    await dialog_manager.next()


async def on_health_entered(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
) -> None:
    dialog_manager.dialog_data["health_notes"] = text
    await dialog_manager.switch_to(ClientRegisterSG.injuries)


async def on_health_skip(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["health_notes"] = None
    await dialog_manager.switch_to(ClientRegisterSG.injuries)


async def on_injuries_entered(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str,
) -> None:
    dialog_manager.dialog_data["injuries"] = text
    await dialog_manager.switch_to(ClientRegisterSG.confirm)


async def on_injuries_skip(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["injuries"] = None
    await dialog_manager.switch_to(ClientRegisterSG.confirm)


@inject
async def on_register_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    data = dialog_manager.dialog_data
    user = callback.from_user

    try:
        await mediator.handle(
            RegisterClientRequest(
                tg_id=user.id,
                trainer_id=trainer_id,
                first_name=data["first_name"],
                last_name=data.get("last_name"),
                username=user.username,
                phone=data["phone"],
                age=data["age"],
                sport_experience=data["sport_experience"],
                health_conditions=data.get("health_conditions", []),
                health_conditions_other=data.get("health_conditions_other_text"),
                goals=data.get("goals", []),
                health_notes=data.get("health_notes"),
                injuries=data.get("injuries"),
            )
        )
    except AssigningClientToAnotherTrainerError:
        await callback.answer(
            "Вы уже зарегистрированы у другого тренера в этом боте",
            show_alert=True,
        )
        return

    await dialog_manager.start(
        ClientMenuSG.main,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": trainer_id},
    )