from dataclasses import dataclass
from html import escape
import logging

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.entities.client_answer import ClientAnswer
from src.domain.enums.training import SportExperience
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_answer import ClientAnswerRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class RegisterClientRequest(UseCaseRequest):
    tg_id: int
    trainer_id: int
    first_name: str
    last_name: str | None
    username: str | None
    phone: str
    age: int
    sport_experience: str
    answers: dict[str, list[str]]  # question_id (str) -> value
    # пришёл по ссылке «пригласить друга» другого клиента
    referred_by_client_id: int | None = None


@dataclass(kw_only=True)
class RegisterClientUseCase(UseCase[RegisterClientRequest, Client]):
    client_repo: ClientRepository
    answer_repo: ClientAnswerRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: RegisterClientRequest) -> Client:
        logger.info("[RegisterClient] tg_id=%s trainer_id=%s", command.tg_id, command.trainer_id)

        existing = await self.client_repo.get_by_tg_id(command.tg_id)
        if existing is not None:
            existing.assingn_trainer(command.trainer_id)
            logger.info("[RegisterClient:already_registered] client_id=%s", existing.id)
            return existing

        client = Client(
            tg_id=command.tg_id,
            trainer_id=command.trainer_id,
            first_name=command.first_name,
            last_name=command.last_name,
            username=command.username,
            phone=command.phone,
            age=command.age,
            sport_experience=SportExperience(command.sport_experience),
            referred_by_client_id=await self._referrer_id(command),
        )
        saved = await self.client_repo.save(client)

        answers = [
            ClientAnswer(client_id=saved.id, question_id=int(qid), value=value)
            for qid, value in command.answers.items()
        ]
        if answers:
            await self.answer_repo.save_many(answers)

        await self.transaction_manager.commit()

        if saved.referred_by_client_id is not None:
            await self._notify_referral(saved)

        logger.info("[RegisterClient:done] client_id=%s", saved.id)
        return saved

    async def _referrer_id(self, command: RegisterClientRequest) -> int | None:
        if command.referred_by_client_id is None:
            return None
        referrer = await self.client_repo.get_by_id(command.referred_by_client_id)
        # приглашение действует только к тренеру того, кто пригласил
        if referrer is None or referrer.trainer_id != command.trainer_id:
            return None
        return referrer.id

    async def _notify_referral(self, client: Client) -> None:
        referrer = await self.client_repo.get_by_id(client.referred_by_client_id)
        trainer = await self.trainer_repo.get_by_id(client.trainer_id)
        if referrer is None or trainer is None:
            return
        await self.notification_service.send(
            chat_id=trainer.notification_chat_id,
            text=(
                f"🎁 Новый клиент <b>{escape(client.full_name)}</b> пришёл по приглашению "
                f"<b>{escape(referrer.full_name)}</b>."
            ),
        )
        if referrer.has_telegram:
            await self.notification_service.send(
                chat_id=referrer.tg_id,
                text=(
                    f"🎉 Ваш друг <b>{escape(client.full_name)}</b> присоединился к тренировкам "
                    f"у {escape(trainer.name)}. Спасибо, что рекомендуете!"
                ),
            )