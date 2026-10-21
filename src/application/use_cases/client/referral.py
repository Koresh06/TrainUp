import secrets
from dataclasses import dataclass, field

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.exception.client import ClientInviteNotFoundException, ClientNotFoundException
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

# префикс deep-link'а «пригласить друга» (у ссылки тренера — token_urlsafe,
# у персональной ссылки карточки — «cl_»)
REFERRAL_PREFIX = "ref_"


@dataclass(frozen=True)
class ReferralInfoDTO:
    code: str
    bonus_sessions: int
    invited: list[Client] = field(default_factory=list)

    @property
    def rewarded(self) -> int:
        return sum(1 for c in self.invited if c.referral_rewarded_at is not None)


@dataclass(frozen=True, eq=False)
class GetReferralInfoRequest(UseCaseRequest):
    client_id: int


@dataclass(kw_only=True)
class GetReferralInfoUseCase(UseCase[GetReferralInfoRequest, ReferralInfoDTO]):
    """Код для ссылки «пригласить друга» (создаётся при первом обращении) и итоги."""

    client_repo: ClientRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: GetReferralInfoRequest) -> ReferralInfoDTO:
        client = await self.client_repo.get_by_id(command.client_id)
        if client is None:
            raise ClientNotFoundException(client_id=command.client_id)
        if client.referral_code is None:
            client.referral_code = secrets.token_hex(5)
            client = await self.client_repo.save(client)
            await self.transaction_manager.commit()
        settings = await self.booking_settings_repo.get_by_trainer_id(client.trainer_id)
        return ReferralInfoDTO(
            code=client.referral_code,
            bonus_sessions=settings.referral_bonus_sessions if settings else 0,
            invited=await self.client_repo.get_referred_by(client.id),
        )


@dataclass(frozen=True, eq=False)
class ResolveReferralCodeRequest(UseCaseRequest):
    code: str


@dataclass(kw_only=True)
class ResolveReferralCodeUseCase(UseCase[ResolveReferralCodeRequest, Client]):
    client_repo: ClientRepository

    async def __call__(self, command: ResolveReferralCodeRequest) -> Client:
        referrer = await self.client_repo.get_by_referral_code(command.code)
        if referrer is None or not referrer.is_active:
            raise ClientInviteNotFoundException(token=command.code)
        return referrer
