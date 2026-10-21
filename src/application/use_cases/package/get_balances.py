from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.package._shared import ClientBalanceDTO, build_balances
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client_package import ClientPackageRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository


@dataclass(frozen=True, eq=False)
class GetClientBalancesRequest(UseCaseRequest):
    """Абонементы и долги клиентов тренера; client_id — только одного клиента."""

    trainer_id: int
    client_id: int | None = None


@dataclass(kw_only=True)
class GetClientBalancesUseCase(UseCase[GetClientBalancesRequest, dict[int, ClientBalanceDTO]]):
    booking_repo: BookingRepository
    package_repo: ClientPackageRepository
    booking_settings_repo: TrainerBookingSettingsRepository

    async def __call__(self, command: GetClientBalancesRequest) -> dict[int, ClientBalanceDTO]:
        return await build_balances(
            trainer_id=command.trainer_id,
            client_id=command.client_id,
            booking_repo=self.booking_repo,
            package_repo=self.package_repo,
            booking_settings_repo=self.booking_settings_repo,
        )
