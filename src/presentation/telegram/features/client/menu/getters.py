from html import escape
from urllib.parse import quote

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.enums.booking import BookingStatus
from src.application.mediator import Mediator
from src.application.use_cases.client.referral import (
    REFERRAL_PREFIX,
    GetReferralInfoRequest,
    ReferralInfoDTO,
)
from src.application.services.referral_reward import REFERRAL_BONUS_VALID_DAYS
from src.application.use_cases.package.create import sessions_word
from src.core.config import settings
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
            f'🔗 <a href="{escape(url)}">{escape(name)}</a>'
            for name, url in trainer.social_links.items()
        )
        social_links_block = f"\n\n{links}"

    return {
        "trainer_name": escape(trainer.name),
        "trainer_bio": escape(trainer.bio),
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

    _WEEKDAY_SHORT = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    lines = []
    for booking in bookings:
        slot: CalendarSlot = await mediator.handle(
            GetSlotByIdRequest(slot_id=booking.slot_id)
        )
        status = CLIENT_BOOKING_STATUS_LABELS.get(booking.status, "")
        recurring_mark = " 🔁" if booking.recurring_booking_id is not None else ""
        weekday = _WEEKDAY_SHORT[slot.slot_date.weekday()]
        lines.append(
            f"<b>{slot.slot_date.strftime('%d.%m')}</b> ({weekday})"
            f"  🕐 <b>{slot.start_time.strftime('%H:%M')}</b>{recurring_mark}\n"
            f"   {status}"
        )

    contact = f'<a href="tg://user?id={trainer.tg_id}">написать тренеру</a>'
    if trainer.phone:
        contact += f" · 📞 {trainer.phone}"

    return {
        "bookings_block": "\n\n".join(lines) if lines else "У вас пока нет предстоящих записей 🗓",
        "contact_hint": (
            f"ℹ️ Чтобы отменить — {contact}\n"
            f"🔁 — постоянная тренировка"
            if lines
            else "Записаться можно в разделе «📅 Записаться на тренировку»."
        ),
    }


@inject
async def referral_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=dialog_manager.event.from_user.id)
    )
    info: ReferralInfoDTO = await mediator.handle(GetReferralInfoRequest(client_id=client.id))
    link = f"https://t.me/{settings.telegram.bot_username}?start={REFERRAL_PREFIX}{info.code}"
    trainer: Trainer = await mediator.handle(GetTrainerByIdRequest(trainer_id=client.trainer_id))

    steps = [
        f"1️⃣ Отправьте другу ссылку ниже — по ней он попадёт к вашему тренеру "
        f"<b>{escape(trainer.name)}</b>.",
        "2️⃣ Друг регистрируется в боте и записывается на тренировку.",
    ]
    if info.bonus_sessions:
        steps.append(
            f"3️⃣ Как только он <b>сходит на первую тренировку</b>, вам начислится "
            f"<b>{info.bonus_sessions} {sessions_word(info.bonus_sessions)} бесплатно</b>. "
            f"Они спишутся сами на ваших ближайших тренировках, действуют "
            f"{REFERRAL_BONUS_VALID_DAYS} дней — остаток видно в «📝 Моя анкета»."
        )
        rules = "Бонус — за каждого друга, сколько угодно раз."
    else:
        steps.append(
            "3️⃣ Сейчас тренер не начисляет бонусы за приглашения, но всегда рад "
            "новым людям на тренировках 💪"
        )
        rules = ""

    if info.invited:
        lines = [
            f"• {escape(c.first_name)} — "
            + (
                "✅ сходил(а) на тренировку" + (", бонус начислен" if info.bonus_sessions else "")
                if c.referral_rewarded_at
                else "⏳ ждём первую тренировку"
            )
            for c in info.invited
        ]
        invited = f"👥 <b>Вы пригласили: {len(info.invited)}</b>\n" + "\n".join(lines)
    else:
        invited = "👥 Пока никого — станьте первым 🙂"
    return {
        "steps": "\n".join(steps),
        "rules": f"\n\n<i>{rules}</i>" if rules else "",
        "link": link,
        "invited": invited,
        "share_url": f"https://t.me/share/url?url={quote(link)}&text={quote('Тренируйся со мной 💪')}",
    }
