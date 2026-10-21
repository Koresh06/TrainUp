from dataclasses import dataclass
from enum import Enum

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client_package import ClientPackage
from src.domain.exception.package import PackageNotFoundException
from src.domain.repositories.client_package import ClientPackageRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


class PackageAction(str, Enum):
    MARK_PAID = "mark_paid"
    CANCEL = "cancel"


@dataclass(frozen=True, eq=False)
class ManageClientPackageRequest(UseCaseRequest):
    trainer_id: int
    package_id: int
    action: PackageAction


@dataclass(kw_only=True)
class ManageClientPackageUseCase(UseCase[ManageClientPackageRequest, ClientPackage]):
    """Тренер отмечает оплату абонемента или закрывает его (возврат, ошибка)."""

    package_repo: ClientPackageRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: ManageClientPackageRequest) -> ClientPackage:
        package = await self.package_repo.get_by_id(command.package_id)
        if package is None or package.trainer_id != command.trainer_id:
            raise PackageNotFoundException(package_id=command.package_id)

        if command.action == PackageAction.MARK_PAID:
            package.mark_paid()
        else:
            package.cancel()
        saved = await self.package_repo.save(package)
        await self.transaction_manager.commit()
        return saved
