from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.domain.constants import WEEKDAY_LABELS_FULL
from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.enums.booking import BookingStatus
from src.application.mediator import Mediator
from src.application.use_cases.booking.get_upcoming_by_client import (
    GetUpcomingBookingsByClientRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.presentation.telegram.build_media import build_media_attachment

CLIENT_BOOKING_STATUS_LABELS: dict[BookingStatus, str] = {
    BookingStatus.PENDING: "⏳ ожидает подтверждения тренера",
    BookingStatus.CONFIRMED: "✅ подтверждена",
}


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


@inject
async def my_bookings_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=dialog_manager.event.from_user.id)
    )
    bookings: list[Booking] = await mediator.handle(
        GetUpcomingBookingsByClientRequest(client_id=client.id)
    )
    trainer: Trainer = await mediator.handle(
        GetTrainerByIdRequest(trainer_id=trainer_id)
    )

    lines = []
    for booking in bookings:
        slot: CalendarSlot = await mediator.handle(
            GetSlotByIdRequest(slot_id=booking.slot_id)
        )
        status = CLIENT_BOOKING_STATUS_LABELS.get(booking.status, "")
        recurring_mark = " 🔁" if booking.recurring_booking_id is not None else ""
        lines.append(
            f"📅 {slot.slot_date.strftime('%d.%m.%Y')} "
            f"({WEEKDAY_LABELS_FULL[slot.slot_date.weekday()].lower()}) "
            f"в {slot.start_time.strftime('%H:%M')}{recurring_mark}\n"
            f"     {status}"
        )

    contact = f'<a href="tg://user?id={trainer.tg_id}">написать тренеру</a>'
    if trainer.phone:
        contact += f" или позвонить: {trainer.phone}"

    return {
        "bookings_block": "\n\n".join(lines) if lines else "У вас пока нет предстоящих записей.",
        "contact_hint": (
            f"ℹ️ Чтобы отменить или перенести тренировку — {contact}.\n"
            f"🔁 — постоянная тренировка."
            if lines
            else "Записаться можно в разделе «📅 Записаться на занятия»."
        ),
    }
