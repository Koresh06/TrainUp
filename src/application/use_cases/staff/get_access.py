from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.bot_admin import AdminAccess
from src.domain.repositories.bot_admin import BotAdminRepository


@dataclass(frozen=True, eq=False)
class GetAdminAccessRequest(UseCaseRequest):
    tg_id: int


@dataclass(kw_only=True)
class GetAdminAccessUseCase(UseCase[GetAdminAccessRequest, AdminAccess | None]):
    """None — не админ. Супер-админа определяем без БД: доступ из .env должен
    работать, даже если таблица пуста или с ней что-то случилось."""

    admin_repo: BotAdminRepository
    super_admin_ids: list[int]

    async def __call__(self, command: GetAdminAccessRequest) -> AdminAccess | None:
        if command.tg_id in self.super_admin_ids:
            return AdminAccess(tg_id=command.tg_id, is_super=True)
        admin = await self.admin_repo.get_by_tg_id(command.tg_id)
        if admin is None:
            return None
        return AdminAccess(
            tg_id=admin.tg_id,
            is_super=False,
            permissions=frozenset(admin.permissions),
        )
