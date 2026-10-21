import logging
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client._shared import get_trainer_client
from src.domain.entities.client_package import ClientPackage
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_package import ClientPackageRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.utils import get_project_today
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now

logger = logging.getLogger(__name__)


def sessions_word(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return "занятие"
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "занятия"
    return "занятий"


@dataclass(frozen=True, eq=False)
class CreateClientPackageRequest(UseCaseRequest):
    trainer_id: int
    client_id: int
    sessions_total: int
    price: Decimal | None = None
    # None — бессрочный
    valid_days: int | None = None
    paid: bool = False
    title: str | None = None
    is_bonus: bool = False
    notify_client: bool = True


@dataclass(kw_only=True)
class CreateClientPackageUseCase(UseCase[CreateClientPackageRequest, ClientPackage]):
    package_repo: ClientPackageRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateClientPackageRequest) -> ClientPackage:
        if command.sessions_total <= 0:
            raise ValueError("sessions_total must be positive")
        client = await get_trainer_client(
            self.client_repo, client_id=command.client_id, trainer_id=command.trainer_id
        )
        package = ClientPackage(
            trainer_id=command.trainer_id,
            client_id=client.id,
            title=command.title
            or f"{command.sessions_total} {sessions_word(command.sessions_total)}",
            sessions_total=command.sessions_total,
            price=command.price,
            valid_until=(
                get_project_today() + timedelta(days=command.valid_days)
                if command.valid_days
                else None
            ),
            paid_at=get_datetime_utc_now() if command.paid else None,
            is_bonus=command.is_bonus,
        )
        saved = await self.package_repo.save(package)
        await self.transaction_manager.commit()

        if command.notify_client and client.has_telegram:
            trainer = await self.trainer_repo.get_by_id(command.trainer_id)
            until = (
                f" до {saved.valid_until.strftime('%d.%m.%Y')}" if saved.valid_until else ""
            )
            await self.notification_service.send(
                chat_id=client.tg_id,
                text=(
                    f"🎫 <b>Абонемент «{escape(saved.title)}»</b> оформлен"
                    f"{f' у тренера {escape(trainer.name)}' if trainer else ''}{until}.\n\n"
                    f"Занятия списываются автоматически после тренировки, остаток — "
                    f"в «📝 Моя анкета»."
                ),
            )
        logger.info("[CreateClientPackage:done] package_id=%s client_id=%s", saved.id, client.id)
        return saved
