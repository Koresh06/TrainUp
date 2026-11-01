from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer import Trainer
from src.domain.enums.trainer import TrainerApprovalStatus
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True, eq=False)
class GetTrainerApplicationsRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class GetTrainerApplicationsUseCase(
    UseCase[GetTrainerApplicationsRequest, list[Trainer]]
):
    """Нерешённые заявки, затем отклонённые — их можно одобрить позже."""

    trainer_repo: TrainerRepository

    async def __call__(self, command: GetTrainerApplicationsRequest) -> list[Trainer]:
        trainers = await self.trainer_repo.get_all()
        return [
            trainer
            for status in (TrainerApprovalStatus.PENDING, TrainerApprovalStatus.REJECTED)
            for trainer in trainers
            if trainer.approval_status == status
        ]
