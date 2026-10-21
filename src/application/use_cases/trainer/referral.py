import secrets
from dataclasses import dataclass, field

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import TRAINER_REFERRAL_BONUS_DAYS, TRAINER_REFERRAL_FRIEND_DAYS
from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

# префикс deep-link'а «пригласить тренера» (у клиентской программы — «ref_»)
TRAINER_REFERRAL_PREFIX = "tr_"


@dataclass(frozen=True)
class TrainerReferralInfoDTO:
    code: str
    bonus_days: int   # пригласившему — после первой оплаты приглашённого
    friend_days: int  # приглашённому — к пробному периоду
    invited: list[Trainer] = field(default_factory=list)

    @property
    def rewarded(self) -> int:
        return sum(1 for t in self.invited if t.referral_rewarded_at is not None)


@dataclass(frozen=True, eq=False)
class GetTrainerReferralInfoRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetTrainerReferralInfoUseCase(UseCase[GetTrainerReferralInfoRequest, TrainerReferralInfoDTO]):
    """Код ссылки «пригласить тренера» (создаётся при первом обращении) и итоги."""

    trainer_repo: TrainerRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: GetTrainerReferralInfoRequest) -> TrainerReferralInfoDTO:
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)
        if trainer.referral_code is None:
            trainer.referral_code = secrets.token_hex(5)
            trainer = await self.trainer_repo.save(trainer)
            await self.transaction_manager.commit()
        return TrainerReferralInfoDTO(
            code=trainer.referral_code,
            bonus_days=TRAINER_REFERRAL_BONUS_DAYS,
            friend_days=TRAINER_REFERRAL_FRIEND_DAYS,
            invited=await self.trainer_repo.get_referred_by(trainer.id),
        )


@dataclass(frozen=True, eq=False)
class ResolveTrainerReferralCodeRequest(UseCaseRequest):
    code: str


@dataclass(kw_only=True)
class ResolveTrainerReferralCodeUseCase(UseCase[ResolveTrainerReferralCodeRequest, Trainer | None]):
    trainer_repo: TrainerRepository

    async def __call__(self, command: ResolveTrainerReferralCodeRequest) -> Trainer | None:
        trainer = await self.trainer_repo.get_by_referral_code(command.code)
        return trainer if trainer is not None and trainer.is_active else None
