from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.exception.invite_link import (
    TrainerInviteLinkAlreadyExistsException,
    TrainerInviteLinkNotFoundException,
)
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.infrastructure.database.models import TrainerInviteLinkModel


class SQLAlchemyTrainerInviteLinkRepo(TrainerInviteLinkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_token(self, token: str) -> TrainerInviteLink | None:
        query = select(TrainerInviteLinkModel).where(TrainerInviteLinkModel.token == token)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def get_active_by_trainer_id(self, trainer_id: int) -> TrainerInviteLink | None:
        query = select(TrainerInviteLinkModel).where(
            TrainerInviteLinkModel.trainer_id == trainer_id,
            TrainerInviteLinkModel.is_active.is_(True),
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, invite_link: TrainerInviteLink) -> None:
        if invite_link.id == 0:
            model = TrainerInviteLinkModel.from_entity(invite_link)
            self._session.add(model)
        else:
            query = select(TrainerInviteLinkModel).where(
                TrainerInviteLinkModel.id == invite_link.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise TrainerInviteLinkNotFoundException(invite_link_id=invite_link.id)
            model.update_model(invite_link)

        try:
            await self._session.flush()
        except IntegrityError as error:
            await self._session.rollback()
            raise TrainerInviteLinkAlreadyExistsException(token=invite_link.token) from error
