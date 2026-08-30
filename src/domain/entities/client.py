from dataclasses import dataclass

from src.domain.entities.base import Entity
from src.domain.enums.training import SportExperience
from src.domain.exception.client import AssigningClientToAnotherTrainerError


@dataclass(kw_only=True)
class Client(Entity):
    tg_id: int
    trainer_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    phone: str
    age: int
    sport_experience: SportExperience
    is_active: bool = True

    def assingn_trainer(self, other_trainer_id: int) -> None:
        if self.trainer_id != other_trainer_id:
            raise AssigningClientToAnotherTrainerError(
                client_id=self.id,
                trainer_id=self.trainer_id,
            )