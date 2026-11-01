from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.bot_admin import BotAdmin
from src.domain.exception.admin import AdminNotFoundException
from src.domain.repositories.bot_admin import BotAdminRepository


@dataclass(frozen=True, eq=False)
class GetAdminsRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class GetAdminsUseCase(UseCase[GetAdminsRequest, list[BotAdmin]]):
    admin_repo: BotAdminRepository
    super_admin_ids: list[int]

    async def __call__(self, command: GetAdminsRequest) -> list[BotAdmin]:
        # у супер-админа строка бывает только ради настроек уведомлений
        return [
            admin
            for admin in await self.admin_repo.get_all()
            if admin.tg_id not in self.super_admin_ids
        ]


@dataclass(frozen=True, eq=False)
class GetAdminRequest(UseCaseRequest):
    tg_id: int


@dataclass(kw_only=True)
class GetAdminUseCase(UseCase[GetAdminRequest, BotAdmin]):
    admin_repo: BotAdminRepository

    async def __call__(self, command: GetAdminRequest) -> BotAdmin:
        admin = await self.admin_repo.get_by_tg_id(command.tg_id)
        if admin is None:
            raise AdminNotFoundException(tg_id=command.tg_id)
        return admin
