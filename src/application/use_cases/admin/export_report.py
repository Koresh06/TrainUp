import csv
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import PROJECT_TIMEZONE
from src.domain.enums.booking import BookingStatus
from src.domain.enums.subscription import PAID_SUBSCRIPTION_SOURCES
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository


class ReportKind(str, Enum):
    TRAINERS = "trainers"
    CLIENTS = "clients"
    BOOKINGS = "bookings"
    PAYMENTS = "payments"


REPORT_KIND_LABELS: dict[ReportKind, str] = {
    ReportKind.TRAINERS: "👨‍🏫 Тренеры",
    ReportKind.CLIENTS: "👥 Клиенты",
    ReportKind.BOOKINGS: "📅 Тренировки",
    ReportKind.PAYMENTS: "💳 Подписки и оплаты",
}


@dataclass(frozen=True)
class ExportFileDTO:
    filename: str
    content: bytes
    rows: int


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PROJECT_TIMEZONE).strftime("%d.%m.%Y %H:%M")


@dataclass(frozen=True, eq=False)
class ExportReportRequest(UseCaseRequest):
    kind: ReportKind


@dataclass(kw_only=True)
class ExportReportUseCase(UseCase[ExportReportRequest, ExportFileDTO]):
    """CSV-выгрузки для админки (разделитель «;» и BOM — Excel открывает сразу)."""

    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    booking_repo: BookingRepository
    slot_repo: CalendarSlotRepository
    subscription_repo: TrainerSubscriptionRepository

    async def __call__(self, command: ExportReportRequest) -> ExportFileDTO:
        builders = {
            ReportKind.TRAINERS: self._trainers,
            ReportKind.CLIENTS: self._clients,
            ReportKind.BOOKINGS: self._bookings,
            ReportKind.PAYMENTS: self._payments,
        }
        header, rows = await builders[command.kind]()

        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)

        stamp = datetime.now(PROJECT_TIMEZONE).strftime("%Y%m%d_%H%M")
        return ExportFileDTO(
            filename=f"trainup_{command.kind.value}_{stamp}.csv",
            content=buffer.getvalue().encode("utf-8-sig"),
            rows=len(rows),
        )

    async def _trainers(self) -> tuple[list[str], list[list]]:
        trainers = await self.trainer_repo.get_all()
        clients = await self.client_repo.get_all()
        subscriptions = await self.subscription_repo.get_all()
        now = datetime.now(timezone.utc)

        clients_count: dict[int, int] = {}
        for c in clients:
            clients_count[c.trainer_id] = clients_count.get(c.trainer_id, 0) + 1

        rows = []
        for t in sorted(trainers, key=lambda t: t.id):
            own = [s for s in subscriptions if s.trainer_id == t.id]
            active = [s for s in own if s.is_active(now)]
            paid = sum((s.amount for s in own if s.source in PAID_SUBSCRIPTION_SOURCES), Decimal("0"))
            rows.append([
                t.id, t.name, t.phone or "", t.tg_id,
                "активен" if t.is_active else "заблокирован",
                _fmt_dt(max((s.expired_at for s in active), default=None)),
                clients_count.get(t.id, 0), f"{paid:.2f}", _fmt_dt(t.created_at),
            ])
        return (
            ["ID", "Имя", "Телефон", "Telegram ID", "Статус", "Подписка до",
             "Клиентов", "Оплачено всего", "Зарегистрирован"],
            rows,
        )

    async def _clients(self) -> tuple[list[str], list[list]]:
        clients = await self.client_repo.get_all()
        names = {t.id: t.name for t in await self.trainer_repo.get_all()}
        rows = [
            [
                c.id, f"{c.first_name} {c.last_name or ''}".strip(), c.phone,
                f"@{c.username}" if c.username else "", c.tg_id, c.age,
                names.get(c.trainer_id, ""),
                "активен" if c.is_active else "заблокирован", _fmt_dt(c.created_at),
            ]
            for c in sorted(clients, key=lambda c: c.id)
        ]
        return (
            ["ID", "Имя", "Телефон", "Username", "Telegram ID", "Возраст", "Тренер",
             "Статус", "Зарегистрирован"],
            rows,
        )

    async def _bookings(self) -> tuple[list[str], list[list]]:
        bookings = await self.booking_repo.get_all()
        slots = {s.id: s for s in await self.slot_repo.get_by_ids([b.slot_id for b in bookings])}
        trainers = {t.id: t.name for t in await self.trainer_repo.get_all()}
        clients = {
            c.id: f"{c.first_name} {c.last_name or ''}".strip()
            for c in await self.client_repo.get_all()
        }
        status_labels = {
            BookingStatus.PENDING: "ожидает",
            BookingStatus.CONFIRMED: "подтверждена",
            BookingStatus.CANCELLED: "отменена",
            BookingStatus.COMPLETED: "проведена",
        }
        rows = []
        for b in sorted(bookings, key=lambda b: b.id):
            slot = slots.get(b.slot_id)
            rows.append([
                b.id,
                slot.slot_date.strftime("%d.%m.%Y") if slot else "",
                slot.start_time.strftime("%H:%M") if slot else "",
                trainers.get(b.trainer_id, ""), clients.get(b.client_id, ""),
                status_labels[b.status], f"{b.price:.2f}" if b.price is not None else "",
                "да" if b.recurring_booking_id else "нет",
            ])
        return (
            ["ID", "Дата", "Время", "Тренер", "Клиент", "Статус", "Цена", "Постоянная"],
            rows,
        )

    async def _payments(self) -> tuple[list[str], list[list]]:
        subscriptions = await self.subscription_repo.get_all()
        trainers = {t.id: t.name for t in await self.trainer_repo.get_all()}
        source_labels = {"purchase": "оплата в боте", "cash": "наличные/перевод", "trial": "бесплатно"}
        rows = [
            [
                s.id, trainers.get(s.trainer_id, ""), s.plan.value,
                source_labels.get(s.source.value, s.source.value), f"{s.amount:.2f}",
                _fmt_dt(s.created_at), _fmt_dt(s.expired_at), s.status.value,
            ]
            for s in sorted(subscriptions, key=lambda s: s.id)
        ]
        return (
            ["ID", "Тренер", "Тариф", "Источник", "Сумма", "Оформлена", "Действует до", "Статус"],
            rows,
        )
