from datetime import date
from decimal import Decimal
from typing import Any

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import ChatEvent, DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, ManagedCalendar, Select

from src.application.mediator import Mediator
from src.application.use_cases.booking.create_by_trainer import (
    CreateBookingByTrainerRequest,
)
from src.application.use_cases.booking.mark_paid import MarkBookingsPaidRequest
from src.application.use_cases.package.create import CreateClientPackageRequest
from src.application.use_cases.package.get_balances import GetClientBalancesRequest
from src.application.use_cases.package.manage import (
    ManageClientPackageRequest,
    PackageAction,
)
from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.client.delete_offline import DeleteOfflineClientRequest
from src.application.use_cases.client.update_by_trainer import UpdateClientFieldRequest
from src.domain.entities.client import Client
from src.domain.enums.client import ClientEditableField
from src.domain.exception.booking import (
    ClientAlreadyBookedThisSlotException,
    SlotAlreadyBookedException,
)
from src.domain.exception.calendar_slot import SlotFullException, SlotInPastException
from src.domain.exception.client import ClientHasBookingsException
from src.presentation.telegram.widgets.booking_calendar import AVAILABILITY_CACHE_KEY

from .states import TrainerClientsSG
from .validaters import NAME_MAX_LENGTH, validate_any_phone, validate_note


async def on_clients_start(start_data: Any, dialog_manager: DialogManager) -> None:
    # карточку открыли из расписания — «Назад» вернёт туда, а не в список
    if isinstance(start_data, dict) and start_data.get("client_id"):
        dialog_manager.dialog_data["viewing_client_id"] = start_data["client_id"]
        dialog_manager.dialog_data["from_outside"] = True


async def on_client_item_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["viewing_client_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerClientsSG.detail)


# --- новый клиент без Telegram ---


async def on_add_name_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    value: tuple[str, str | None],
) -> None:
    first_name, last_name = value
    dialog_manager.dialog_data["new_client"] = {"first_name": first_name, "last_name": last_name}
    await dialog_manager.switch_to(TrainerClientsSG.add_phone)


async def on_add_phone_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    value: str,
) -> None:
    dialog_manager.dialog_data["new_client"]["phone"] = value
    await dialog_manager.switch_to(TrainerClientsSG.add_note)


async def on_add_phone_skip(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
) -> None:
    dialog_manager.dialog_data["new_client"]["phone"] = None
    await dialog_manager.switch_to(TrainerClientsSG.add_note)


async def _create_offline_client(
    dialog_manager: DialogManager, mediator: Mediator, note: str | None
) -> None:
    data = dialog_manager.dialog_data.pop("new_client")
    client: Client = await mediator.handle(
        CreateOfflineClientRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            phone=data.get("phone"),
            trainer_note=note,
        )
    )
    dialog_manager.dialog_data["viewing_client_id"] = client.id
    await dialog_manager.switch_to(TrainerClientsSG.detail)


@inject
async def on_add_note_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    value: str,
    mediator: FromDishka[Mediator],
) -> None:
    await _create_offline_client(dialog_manager, mediator, value)


@inject
async def on_add_note_skip(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _create_offline_client(dialog_manager, mediator, None)


# --- редактирование карточки ---


async def on_edit_field_click(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
) -> None:
    dialog_manager.dialog_data["editing_field"] = button.widget_id
    await dialog_manager.switch_to(TrainerClientsSG.edit_value)


def parse_edit_value(dialog_manager: DialogManager, raw: str) -> str:
    field = ClientEditableField(dialog_manager.dialog_data["editing_field"])
    if field == ClientEditableField.PHONE:
        return validate_any_phone(raw)
    if field == ClientEditableField.TRAINER_NOTE:
        return validate_note(raw)
    # имя/фамилия — как ввели: бывают двойные («Анна-Мария», «Петров Водкин»)
    value = raw.strip()
    if not value or len(value) > NAME_MAX_LENGTH:
        raise ValueError(f"Введите от 1 до {NAME_MAX_LENGTH} символов")
    return value


async def _save_field(
    dialog_manager: DialogManager, mediator: Mediator, value: str | None
) -> None:
    await mediator.handle(
        UpdateClientFieldRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            client_id=dialog_manager.dialog_data["viewing_client_id"],
            field=ClientEditableField(dialog_manager.dialog_data["editing_field"]),
            value=value,
        )
    )
    await dialog_manager.switch_to(TrainerClientsSG.detail)


@inject
async def on_edit_value_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    value: str,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        parsed = parse_edit_value(dialog_manager, value)
    except ValueError as error:
        await message.answer(f"❌ {error}")
        return
    await _save_field(dialog_manager, mediator, parsed)


@inject
async def on_edit_value_clear(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _save_field(dialog_manager, mediator, None)


@inject
async def on_delete_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(
            DeleteOfflineClientRequest(
                trainer_id=dialog_manager.start_data["trainer_id"],
                client_id=dialog_manager.dialog_data["viewing_client_id"],
            )
        )
    except ClientHasBookingsException:
        await callback.answer(
            "У клиента есть тренировки — карточку нельзя удалить, иначе пропадёт история",
            show_alert=True,
        )
        await dialog_manager.switch_to(TrainerClientsSG.detail)
        return
    await callback.answer("Карточка удалена")
    await dialog_manager.switch_to(TrainerClientsSG.list)


# --- запись клиента тренером ---


async def on_book_day_clicked(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date,
    **kwargs,
) -> None:
    availability: dict[str, int] = dialog_manager.dialog_data.get(AVAILABILITY_CACHE_KEY, {})
    if availability.get(clicked_date.isoformat(), 0) == 0:
        await callback.answer(
            "На этот день нет свободных слотов — добавьте время в «⚙️ Настройки → Расписание»",
            show_alert=True,
        )
        return
    dialog_manager.dialog_data["book_day"] = clicked_date.isoformat()
    await dialog_manager.switch_to(TrainerClientsSG.book_time)


async def on_book_time_clicked(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["book_slot_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerClientsSG.book_confirm)


@inject
async def on_book_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(
            CreateBookingByTrainerRequest(
                trainer_id=dialog_manager.start_data["trainer_id"],
                client_id=dialog_manager.dialog_data["viewing_client_id"],
                slot_id=dialog_manager.dialog_data["book_slot_id"],
            )
        )
    except ClientAlreadyBookedThisSlotException:
        await callback.answer("Клиент уже записан на это время", show_alert=True)
        return
    except SlotFullException:
        await callback.answer("На это время мест уже нет", show_alert=True)
        await dialog_manager.switch_to(TrainerClientsSG.book_time)
        return
    except (SlotAlreadyBookedException, SlotInPastException):
        await callback.answer("Это время уже недоступно", show_alert=True)
        await dialog_manager.switch_to(TrainerClientsSG.book_time)
        return
    await callback.answer("✅ Клиент записан")
    await dialog_manager.switch_to(TrainerClientsSG.detail)


# --- абонементы ---


async def on_package_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data["package_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerClientsSG.package_detail)


async def _sessions_chosen(dialog_manager: DialogManager, sessions: int) -> None:
    dialog_manager.dialog_data["new_package"] = {"sessions": sessions}
    await dialog_manager.switch_to(TrainerClientsSG.package_price)


async def on_package_sessions_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    await _sessions_chosen(dialog_manager, int(item_id))


async def on_package_sessions_input(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, value: int
) -> None:
    await _sessions_chosen(dialog_manager, value)


async def on_package_price_input(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, value: Decimal
) -> None:
    dialog_manager.dialog_data["new_package"]["price"] = str(value)
    await dialog_manager.switch_to(TrainerClientsSG.package_valid)


async def on_package_price_skip(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
) -> None:
    dialog_manager.dialog_data["new_package"]["price"] = None
    await dialog_manager.switch_to(TrainerClientsSG.package_valid)


async def on_package_valid_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data["new_package"]["valid_days"] = int(item_id) or None
    await dialog_manager.switch_to(TrainerClientsSG.package_paid)


async def _create_package(dialog_manager: DialogManager, mediator: Mediator, paid: bool) -> None:
    data = dialog_manager.dialog_data.pop("new_package")
    await mediator.handle(
        CreateClientPackageRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            client_id=dialog_manager.dialog_data["viewing_client_id"],
            sessions_total=data["sessions"],
            price=Decimal(data["price"]) if data.get("price") else None,
            valid_days=data.get("valid_days"),
            paid=paid,
        )
    )
    await dialog_manager.switch_to(TrainerClientsSG.packages)


@inject
async def on_package_create_paid(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _create_package(dialog_manager, mediator, paid=True)
    await callback.answer("🎫 Абонемент оформлен")


@inject
async def on_package_create_unpaid(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _create_package(dialog_manager, mediator, paid=False)
    await callback.answer("🎫 Абонемент оформлен")


async def _manage_package(
    dialog_manager: DialogManager, mediator: Mediator, action: PackageAction
) -> None:
    await mediator.handle(
        ManageClientPackageRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            package_id=dialog_manager.dialog_data["package_id"],
            action=action,
        )
    )


@inject
async def on_package_mark_paid(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _manage_package(dialog_manager, mediator, PackageAction.MARK_PAID)
    await callback.answer("✅ Оплата отмечена")


@inject
async def on_package_close(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _manage_package(dialog_manager, mediator, PackageAction.CANCEL)
    await callback.answer("Абонемент закрыт")
    await dialog_manager.switch_to(TrainerClientsSG.packages)


# --- оплаты разовых тренировок ---


async def _mark_paid(dialog_manager: DialogManager, mediator: Mediator, booking_ids: list[int]) -> None:
    await mediator.handle(
        MarkBookingsPaidRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            booking_ids=tuple(booking_ids),
        )
    )


@inject
async def on_unpaid_booking_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    await _mark_paid(dialog_manager, mediator, [int(item_id)])
    await callback.answer("✅ Оплачено")


@inject
async def on_all_paid(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    client_id: int = dialog_manager.dialog_data["viewing_client_id"]
    balance = (
        await mediator.handle(GetClientBalancesRequest(trainer_id=trainer_id, client_id=client_id))
    )[client_id]
    await _mark_paid(dialog_manager, mediator, [v.booking.id for v in balance.unpaid_bookings])
    await callback.answer("✅ Всё оплачено")
    await dialog_manager.switch_to(TrainerClientsSG.detail)


async def on_debtor_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data["viewing_client_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerClientsSG.detail)
