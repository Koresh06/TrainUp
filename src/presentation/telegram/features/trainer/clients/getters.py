from datetime import date
from decimal import Decimal
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.get_views import GetBookingViewsRequest
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.client.get_answers_by_id import GetClientAnswersRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client.get_inactive import (
    GetInactiveClientsRequest,
    InactiveClientDTO,
)
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerRequest,
)
from src.application.use_cases.package._shared import ClientBalanceDTO
from src.application.use_cases.package.get_balances import GetClientBalancesRequest
from src.application.use_cases.package.get_by_client import GetClientPackagesRequest
from src.application.use_cases.registration_questions.get_all import (
    GetAllRegistrationQuestionsRequest,
)
from src.core.config import settings
from src.application.use_cases.client._shared import CLIENT_INVITE_PREFIX
from src.domain.constants import CALENDAR_BUFFER_DAYS, INACTIVE_CLIENT_DAYS
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.client_answer import ClientAnswer
from src.domain.entities.client_package import ClientPackage
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES, BookingStatus
from src.domain.enums.client import ClientEditableField
from src.domain.enums.package import PackageStatus
from src.domain.enums.training import SPORT_EXPERIENCE_LABELS
from src.domain.repositories.booking import BookingView
from src.domain.utils import get_project_today
from src.utils.timezone import to_moscow
from src.presentation.telegram.common.booking_labels import (
    STATUS_ICONS,
    WEEKDAY_SHORT,
    short_day,
)
from src.presentation.telegram.charts.text import byn
from src.presentation.telegram.common.free_slots import free_slot_options
from src.presentation.telegram.common.package_labels import (
    PACKAGE_STATUS_TITLES,
    package_button_label,
    package_line,
)
from src.presentation.telegram.widgets.booking_calendar import (
    AVAILABILITY_CACHE_KEY,
    HORIZON_CACHE_KEY,
)

UPCOMING_IN_CARD = 5

EDIT_FIELD_PROMPTS: dict[ClientEditableField, str] = {
    ClientEditableField.FIRST_NAME: "Введите имя клиента:",
    ClientEditableField.LAST_NAME: "Введите фамилию клиента:",
    ClientEditableField.PHONE: "Введите телефон клиента:",
    ClientEditableField.TRAINER_NOTE: (
        "Введите заметку о клиенте — её видите только вы\n"
        "(например: «колено, без прыжков», «оплачивает переводом»):"
    ),
}


@inject
async def clients_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer_id)
    )
    recurring: list[RecurringBooking] = await mediator.handle(
        GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer_id)
    )
    recurring_ids = {r.client_id for r in recurring}

    items = []
    for c in clients:
        label = c.full_name
        if c.id in recurring_ids:
            label += " 🔁"
        if not c.has_telegram:
            label = f"📵 {label}"
        items.append({"id": str(c.id), "label": label})

    balances: dict[int, ClientBalanceDTO] = await mediator.handle(
        GetClientBalancesRequest(trainer_id=trainer_id)
    )
    debtors = sum(1 for b in balances.values() if b.debt > 0)
    inactive: list[InactiveClientDTO] = await mediator.handle(
        GetInactiveClientsRequest(trainer_id=trainer_id)
    )

    offline = sum(1 for c in clients if not c.has_telegram)
    summary = f"Всего: {len(clients)}"
    if offline:
        summary += f" · без Telegram 📵: {offline}"
    return {
        "clients": items,
        "summary": summary if clients else "Клиентов пока нет — пригласите по ссылке или добавьте вручную.",
        "debtors_count": debtors,
        "has_debtors": debtors > 0,
        "inactive_count": len(inactive),
        "has_inactive": bool(inactive),
    }


@inject
async def inactive_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    inactive: list[InactiveClientDTO] = await mediator.handle(
        GetInactiveClientsRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )
    return {
        "days": INACTIVE_CLIENT_DAYS,
        "clients": [
            {
                "id": str(dto.client.id),
                "label": (
                    f"{'📵 ' if not dto.client.has_telegram else ''}{dto.client.full_name}"
                    f" — {dto.days_since} дн."
                ),
            }
            for dto in inactive
        ],
    }


@inject
async def debtors_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    clients = {
        c.id: c
        for c in await mediator.handle(GetClientsByTrainerIdRequest(trainer_id=trainer_id))
    }
    balances: dict[int, ClientBalanceDTO] = await mediator.handle(
        GetClientBalancesRequest(trainer_id=trainer_id)
    )
    debtors = sorted(
        (b for b in balances.values() if b.debt > 0 and b.client_id in clients),
        key=lambda b: b.debt,
        reverse=True,
    )
    total = sum((b.debt for b in debtors), Decimal("0"))
    return {
        "clients": [
            {"id": str(b.client_id), "label": f"{clients[b.client_id].full_name} — {byn(b.debt)}"}
            for b in debtors
        ],
        "total": byn(total),
    }


def _contacts(client: Client) -> str:
    lines = []
    if client.has_telegram:
        lines.append(f'💬 <a href="tg://user?id={client.tg_id}">Написать в Telegram</a>')
        if client.username:
            lines.append(f"👤 @{escape(client.username)}")
    else:
        lines.append("📵 Без Telegram — уведомления не получает")
    lines.append(f"📞 {escape(client.phone) if client.phone else '—'}")
    return "\n".join(lines)


async def _client_card_lines(
    mediator: Mediator, trainer_id: int, client: Client
) -> tuple[list[str], bool]:
    today = get_project_today()
    views: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(trainer_id=trainer_id, client_id=client.id)
    )
    upcoming = [
        v for v in views if v.booking.status in ACTIVE_BOOKING_STATUSES and v.slot_date >= today
    ]
    completed = [v for v in views if v.booking.status == BookingStatus.COMPLETED]
    cancelled = sum(1 for v in views if v.booking.status == BookingStatus.CANCELLED)

    lines = []
    if upcoming:
        lines.append("📅 <b>Ближайшие:</b>")
        for v in upcoming[:UPCOMING_IN_CARD]:
            lines.append(
                f"  {STATUS_ICONS.get(v.booking.status, '')} {short_day(v.slot_date)} "
                f"{v.start_time.strftime('%H:%M')}"
                f"{' 🔁' if v.booking.recurring_booking_id else ''}"
            )
        if len(upcoming) > UPCOMING_IN_CARD:
            lines.append(f"  … и ещё {len(upcoming) - UPCOMING_IN_CARD}")
    else:
        lines.append("📅 Будущих записей нет")

    stats = f"📊 Проведено: {len(completed)} · отмен: {cancelled}"
    if completed:
        last: date = max(v.slot_date for v in completed)
        stats += f"\n🕓 Последняя тренировка: {last.strftime('%d.%m.%Y')}"
    lines.append(stats)
    return lines, bool(upcoming)


@inject
async def client_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client_id: int = dialog_manager.dialog_data["viewing_client_id"]
    trainer_id: int = dialog_manager.start_data["trainer_id"]

    client: Client = await mediator.handle(GetClientByIdRequest(client_id=client_id))
    all_clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer_id)
    )

    questions: list[RegistrationQuestion] = await mediator.handle(
        GetAllRegistrationQuestionsRequest(trainer_id=trainer_id)
    )
    answers: list[ClientAnswer] = await mediator.handle(
        GetClientAnswersRequest(client_id=client_id)
    )
    answers_by_question = {a.question_id: a.value for a in answers}
    answers_lines = [
        f"• {escape(q.label)}: {escape(', '.join(answers_by_question[q.id]))}"
        for q in questions
        if answers_by_question.get(q.id)
    ]

    recurring_list: list[RecurringBooking] = await mediator.handle(
        GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer_id)
    )
    client_recurring = sorted(
        (r for r in recurring_list if r.client_id == client_id),
        key=lambda r: (r.weekday, r.start_time),
    )

    lines = [f"👤 <b>{escape(client.full_name)}</b>", _contacts(client)]
    profile = []
    if client.age:
        profile.append(f"🎂 {client.age} лет")
    if client.sport_experience:
        profile.append(f"🏋️ Стаж: {SPORT_EXPERIENCE_LABELS.get(client.sport_experience, '—')}")
    if profile:
        lines.append(" · ".join(profile))
    if client.trainer_note:
        lines.append(f"📝 <i>{escape(client.trainer_note)}</i>")
    if client.referred_by_client_id is not None:
        referrer: Client = await mediator.handle(
            GetClientByIdRequest(client_id=client.referred_by_client_id)
        )
        lines.append(f"🎁 Пришёл по приглашению: {escape(referrer.full_name)}")
    invited = [c for c in all_clients if c.referred_by_client_id == client.id]
    if invited:
        lines.append(f"🎁 Привёл друзей: {len(invited)}")
    if client_recurring:
        lines.append(
            "🔁 Постоянно: "
            + ", ".join(
                f"{WEEKDAY_SHORT[r.weekday]} {r.start_time.strftime('%H:%M')}"
                for r in client_recurring
            )
        )
    lines.append("")
    balance: ClientBalanceDTO = (
        await mediator.handle(GetClientBalancesRequest(trainer_id=trainer_id, client_id=client_id))
    )[client_id]
    today = get_project_today()
    for package in balance.active_packages:
        lines.append(package_line(package, today))
    if balance.unpaid_bookings:
        unpaid_sum = sum((v.booking.price or Decimal("0") for v in balance.unpaid_bookings), Decimal("0"))
        lines.append(
            f"💵 Не оплачено разовых: {len(balance.unpaid_bookings)} на {byn(unpaid_sum)}"
        )
    if balance.active_packages or balance.unpaid_bookings:
        lines.append("")
    card_lines, has_upcoming = await _client_card_lines(mediator, trainer_id, client)
    lines.extend(card_lines)
    if answers_lines:
        lines.append("\n📋 <b>Анкета:</b>\n" + "\n".join(answers_lines))

    return {
        "card": "\n".join(lines),
        "is_offline": not client.has_telegram,
        "from_outside": dialog_manager.dialog_data.get("from_outside", False),
        "has_unpaid": bool(balance.unpaid_bookings),
        # позвать на тренировку можно того, кто в Telegram и никуда не записан
        "can_invite_back": client.has_telegram and not has_upcoming and not client_recurring,
    }


@inject
async def edit_menu_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    return {
        "full_name": escape(client.full_name),
        # имя/фамилию/телефон клиента из Telegram он заполнил сам — тренер
        # правит только заметку, чтобы не разойтись с анкетой
        "is_offline": not client.has_telegram,
    }


async def edit_value_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    field = ClientEditableField(dialog_manager.dialog_data["editing_field"])
    return {
        "prompt": EDIT_FIELD_PROMPTS[field],
        "can_clear": field != ClientEditableField.FIRST_NAME,
    }


@inject
async def invite_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    link = (
        f"https://t.me/{settings.telegram.bot_username}?start={CLIENT_INVITE_PREFIX}{client.invite_token}"
        if client.invite_token
        else None
    )
    return {"full_name": escape(client.full_name), "link": link or "—", "has_link": link is not None}


@inject
async def book_day_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    # тренеру доступен весь материализованный буфер слотов, а не только
    # горизонт записи клиентов
    availability: dict[date, int] = await mediator.handle(
        GetDayAvailabilityMapRequest(trainer_id=trainer_id, days_ahead=CALENDAR_BUFFER_DAYS)
    )
    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = {
        d.isoformat(): count for d, count in availability.items()
    }
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = CALENDAR_BUFFER_DAYS
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    return {"full_name": escape(client.full_name)}


@inject
async def book_time_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    day = date.fromisoformat(dialog_manager.dialog_data["book_day"])
    return {
        "times": await free_slot_options(mediator, trainer_id, day),
        "day_label": short_day(day),
    }


@inject
async def book_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    slot: CalendarSlot = await mediator.handle(
        GetSlotByIdRequest(slot_id=dialog_manager.dialog_data["book_slot_id"])
    )
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    return {
        "full_name": escape(client.full_name),
        "day_label": short_day(slot.slot_date),
        "time": slot.start_time.strftime("%H:%M"),
        "notify_hint": (
            "Клиент получит уведомление и напоминание."
            if client.has_telegram
            else "📵 Клиент без Telegram — предупредите его сами."
        ),
    }


# --- абонементы и оплаты ---

PACKAGE_SESSION_OPTIONS = [4, 8, 10, 12, 16]
PACKAGE_VALID_OPTIONS = [(30, "30 дней"), (60, "60 дней"), (90, "90 дней"), (0, "Без срока")]


@inject
async def packages_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client_id: int = dialog_manager.dialog_data["viewing_client_id"]
    client: Client = await mediator.handle(GetClientByIdRequest(client_id=client_id))
    packages: list[ClientPackage] = await mediator.handle(
        GetClientPackagesRequest(client_id=client_id)
    )
    today = get_project_today()
    return {
        "full_name": escape(client.full_name),
        "packages": [
            {"id": str(p.id), "label": package_button_label(p, today)} for p in packages
        ],
        "empty_hint": (
            ""
            if packages
            else "\n\nАбонементов пока нет. Занятия по абонементу списываются "
            "автоматически после каждой проведённой тренировки."
        ),
    }


@inject
async def package_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client_id: int = dialog_manager.dialog_data["viewing_client_id"]
    package_id: int = dialog_manager.dialog_data["package_id"]
    packages: list[ClientPackage] = await mediator.handle(
        GetClientPackagesRequest(client_id=client_id)
    )
    package = next(p for p in packages if p.id == package_id)
    today = get_project_today()

    lines = [
        f"🎫 <b>{escape(package.title)}</b>",
        f"Использовано {package.sessions_used} из {package.sessions_total}, "
        f"осталось <b>{package.remaining}</b>",
        f"📌 {PACKAGE_STATUS_TITLES[package.status]}"
        + (" · ⌛ срок истёк" if package.is_expired(today) else ""),
    ]
    if package.valid_until:
        lines.append(f"📅 Действует до {package.valid_until.strftime('%d.%m.%Y')}")
    if package.is_bonus:
        lines.append("🎁 Бонусные занятия")
    elif package.price:
        paid = (
            f"✅ оплачен {to_moscow(package.paid_at).strftime('%d.%m.%Y')}"
            if package.paid_at
            else "💵 не оплачен"
        )
        lines.append(f"💰 {byn(package.price)} · {paid}")
    lines.append(f"🗓 Оформлен {to_moscow(package.created_at).strftime('%d.%m.%Y')}")
    return {
        "card": "\n".join(lines),
        "can_pay": not package.is_paid,
        "can_close": package.status == PackageStatus.ACTIVE,
    }


async def package_sessions_getter(**kwargs) -> dict:
    return {
        "options": [{"id": str(n), "label": str(n)} for n in PACKAGE_SESSION_OPTIONS],
    }


async def package_valid_getter(**kwargs) -> dict:
    return {"options": [{"id": str(days), "label": label} for days, label in PACKAGE_VALID_OPTIONS]}


async def package_paid_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data["new_package"]
    price = Decimal(data["price"]) if data.get("price") else None
    valid = f"на {data['valid_days']} дней" if data.get("valid_days") else "без срока"
    return {
        "summary": (
            f"🎫 {data['sessions']} занятий · {valid}"
            + (f" · {byn(price)}" if price else "")
        ),
        "has_price": price is not None,
    }


@inject
async def unpaid_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    client_id: int = dialog_manager.dialog_data["viewing_client_id"]
    balance: ClientBalanceDTO = (
        await mediator.handle(GetClientBalancesRequest(trainer_id=trainer_id, client_id=client_id))
    )[client_id]
    total = sum((v.booking.price or Decimal("0") for v in balance.unpaid_bookings), Decimal("0"))
    return {
        "bookings": [
            {
                "id": str(v.booking.id),
                "label": (
                    f"✅ {short_day(v.slot_date)} {v.start_time.strftime('%H:%M')} · "
                    f"{byn(v.booking.price or 0)}"
                ),
            }
            for v in balance.unpaid_bookings
        ],
        "total": byn(total),
        "has_unpaid": bool(balance.unpaid_bookings),
    }
