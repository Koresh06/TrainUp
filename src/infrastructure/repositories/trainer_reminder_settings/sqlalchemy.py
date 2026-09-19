from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.exception.trainer_reminder_settings import TrainerReminderSettingsNotFoundException
from src.domain.repositories.trainer_reminder_settings import TrainerReminderSettingsRepository
from src.infrastructure.database.models.trainer_reminder_settings import TrainerReminderSettingsModel


class SQLAlchemyTrainerReminderSettingsRepo(TrainerReminderSettingsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_trainer_id(self, trainer_id: int) -> TrainerReminderSettings | None:
        query = select(TrainerReminderSettingsModel).where(
            TrainerReminderSettingsModel.trainer_id == trainer_id
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return model.to_entity() if model is not None else None

    async def save(self, settings: TrainerReminderSettings) -> TrainerReminderSettings:
        if settings.id == 0:
            model = TrainerReminderSettingsModel.from_entity(settings)
            self._session.add(model)
        else:
            model = await self._session.get(TrainerReminderSettingsModel, settings.id)
            if model is None:
                raise TrainerReminderSettingsNotFoundException(settings.id)
            model.update_model(settings)

        await self._session.flush()
        return model.to_entity()