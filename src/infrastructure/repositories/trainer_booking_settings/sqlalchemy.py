from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.trainer_booking_settings import (
    TrainerBookingSettingsRepository,
)
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.exception.trainer_booking_settings import (
    TrainerBookingSettingsNotFoundException,
)
from src.infrastructure.database.models.trainer_booking_settings import (
    TrainerBookingSettingsModel,
)


class SQLAlchemyTrainerBookingSettingsRepo(TrainerBookingSettingsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_trainer_id(self, trainer_id: int) -> TrainerBookingSettings | None:
        query = select(TrainerBookingSettingsModel).where(
            TrainerBookingSettingsModel.trainer_id == trainer_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, settings: TrainerBookingSettings) -> TrainerBookingSettings:
        if settings.id == 0:
            model = TrainerBookingSettingsModel.from_entity(settings)
            self._session.add(model)
        else:
            query = select(TrainerBookingSettingsModel).where(
                TrainerBookingSettingsModel.id == settings.id
            )
            result = await self._session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                raise TrainerBookingSettingsNotFoundException(
                    trainer_id=settings.trainer_id
                )
            model.update_model(settings)

        await self._session.flush()
        return model.to_entity()
