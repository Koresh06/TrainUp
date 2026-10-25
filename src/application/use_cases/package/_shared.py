import logging
from dataclasses import dataclass, field
from decimal import Decimal
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.domain.entities.client_package import ClientPackage
from src.domain.enums.booking import BookingStatus
from src.domain.enums.package import PackageStatus
from src.domain.repositories.booking import BookingRepository, BookingView
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_package import ClientPackageRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.domain.utils import get_project_today

logger = logging.getLogger(__name__)


async def _notify_low_balance(
    package: ClientPackage,
    client_repo: ClientRepository,
    trainer_repo: TrainerRepository,
    notification_service: NotificationService,
) -> None:
    if package.remaining > 1:
        return
    client = await client_repo.get_by_id(package.client_id)
    trainer = await trainer_repo.get_by_id(package.trainer_id)
    if client is None or trainer is None:
        return

    if package.remaining == 1:
        client_text = (
            f"🎫 По абонементу «{escape(package.title)}» осталось <b>1 занятие</b>.\n"
            f"Чтобы не прерывать тренировки, продлите абонемент у тренера {escape(trainer.name)}."
        )
    else:
        client_text = (
            f"🎫 Абонемент «{escape(package.title)}» закончился — все занятия использованы.\n"
            f"Продлите его у тренера {escape(trainer.name)}."
        )
        await notification_service.send(
            chat_id=trainer.notification_chat_id,
            fallback_chat_id=trainer.tg_id,
            text=(
                f"🎫 У клиента <b>{escape(client.full_name)}</b> закончился абонемент "
                f"«{escape(package.title)}». Предложите продление."
            ),
        )
    if client.has_telegram:
        await notification_service.send(chat_id=client.tg_id, text=client_text)


@dataclass(frozen=True)
class ClientBalanceDTO:
    client_id: int
    active_packages: list[ClientPackage] = field(default_factory=list)
    # абонементы, которые ещё не оплачены
    unpaid_packages: list[ClientPackage] = field(default_factory=list)
    # разовые прошедшие тренировки без оплаты
    unpaid_bookings: list[BookingView] = field(default_factory=list)

    @property
    def debt(self) -> Decimal:
        bookings = sum((v.booking.price or Decimal("0") for v in self.unpaid_bookings), Decimal("0"))
        packages = sum((p.price or Decimal("0") for p in self.unpaid_packages), Decimal("0"))
        return bookings + packages


def is_unpaid_single(view: BookingView, no_show_charges: bool) -> bool:
    """Разовая (не по абонементу) прошедшая тренировка с ценой и без отметки об оплате."""
    status = view.booking.status
    chargeable = status == BookingStatus.COMPLETED or (
        status == BookingStatus.NO_SHOW and no_show_charges
    )
    return chargeable and not view.booking.is_paid


async def build_balances(
    *,
    trainer_id: int,
    client_id: int | None,
    booking_repo: BookingRepository,
    package_repo: ClientPackageRepository,
    booking_settings_repo: TrainerBookingSettingsRepository,
) -> dict[int, ClientBalanceDTO]:
    settings = await booking_settings_repo.get_by_trainer_id(trainer_id)
    no_show_charges = settings.no_show_charges_package if settings is not None else True
    today = get_project_today()

    views = await booking_repo.get_views(
        trainer_id=trainer_id,
        client_id=client_id,
        statuses=(BookingStatus.COMPLETED, BookingStatus.NO_SHOW),
    )
    packages = (
        await package_repo.get_by_client(client_id)
        if client_id is not None
        else await package_repo.get_by_trainer(trainer_id)
    )
    packages = [p for p in packages if p.trainer_id == trainer_id]

    client_ids = {v.booking.client_id for v in views} | {p.client_id for p in packages}
    if client_id is not None:
        client_ids.add(client_id)
    return {
        cid: ClientBalanceDTO(
            client_id=cid,
            active_packages=[
                p for p in packages if p.client_id == cid and p.can_charge(today)
            ],
            unpaid_packages=[
                p for p in packages
                if p.client_id == cid and not p.is_paid and p.status != PackageStatus.CANCELLED
            ],
            unpaid_bookings=[
                v for v in views
                if v.booking.client_id == cid and is_unpaid_single(v, no_show_charges)
            ],
        )
        for cid in client_ids
    }
