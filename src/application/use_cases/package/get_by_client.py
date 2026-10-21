from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client_package import ClientPackage
from src.domain.repositories.client_package import ClientPackageRepository


@dataclass(frozen=True, eq=False)
class GetClientPackagesRequest(UseCaseRequest):
    client_id: int


@dataclass(kw_only=True)
class GetClientPackagesUseCase(UseCase[GetClientPackagesRequest, list[ClientPackage]]):
    package_repo: ClientPackageRepository

    async def __call__(self, command: GetClientPackagesRequest) -> list[ClientPackage]:
        return await self.package_repo.get_by_client(command.client_id)
