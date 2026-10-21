from html import escape

from dishka.integrations.aiogram import inject, FromDishka
from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager, StartMode

from src.application.mediator import Mediator
from src.application.use_cases.access.is_trainer_available import (
    IsTrainerAvailableRequest,
)
from src.application.use_cases.client._shared import CLIENT_INVITE_PREFIX
from src.application.use_cases.client.claim_invite import ClaimClientInviteRequest
from src.application.use_cases.client.get_by_invite_token import (
    GetClientByInviteTokenRequest,
)
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.client.referral import (
    REFERRAL_PREFIX,
    ResolveReferralCodeRequest,
)
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.application.use_cases.invite_link.resolve import ResolveInviteLinkRequest
from src.domain.entities.client import Client
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.entities.trainer import Trainer
from src.domain.exception.client import (
    ClientAlreadyExistsException,
    ClientAlreadyHasTelegramException,
    ClientInviteNotFoundException,
    ClientNotFoundException,
)
from src.domain.exception.invite_link import (
    TrainerInviteLinkInactiveException,
    TrainerInviteLinkNotFoundException,
)
from src.presentation.telegram.features.client.register.states import ClientRegisterSG
from src.presentation.telegram.features.client.menu.states import ClientMenuSG
from src.presentation.telegram.middlewares.access import TRAINER_UNAVAILABLE_TEXT

router = Router()

INVALID_CLIENT_INVITE_TEXT = (
    "🚫 Эта персональная ссылка недействительна или уже использована.\n"
    "Попросите тренера прислать новую."
)


class ClaimClientCD(CallbackData, prefix="claim_client"):
    token: str


async def _open_client_menu(dialog_manager: DialogManager, trainer_id: int) -> None:
    await dialog_manager.start(
        state=ClientMenuSG.main,
        data={"trainer_id": trainer_id},
        mode=StartMode.RESET_STACK,
    )


async def _offer_client_claim(message: Message, token: str, mediator: Mediator) -> None:
    """Персональная ссылка из карточки «клиента без Telegram»: сначала просим
    подтвердить, что это он, — ссылку могли переслать не тому человеку."""
    try:
        client: Client = await mediator.handle(GetClientByInviteTokenRequest(token=token))
    except ClientInviteNotFoundException:
        await message.answer(INVALID_CLIENT_INVITE_TEXT)
        return
    trainer: Trainer = await mediator.handle(GetTrainerByIdRequest(trainer_id=client.trainer_id))

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, это я", callback_data=ClaimClientCD(token=token).pack())
    await message.answer(
        f"👋 Тренер <b>{escape(trainer.name)}</b> добавил вас в свои клиенты как "
        f"<b>{escape(client.full_name)}</b>.\n\n"
        f"Подтвердите, что это вы, — и бот будет присылать напоминания о "
        f"тренировках, а записи будут видны в «📋 Мои записи».",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(ClaimClientCD.filter())
@inject
async def on_claim_client_click(
    callback: CallbackQuery,
    callback_data: ClaimClientCD,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        client: Client = await mediator.handle(
            ClaimClientInviteRequest(
                token=callback_data.token,
                tg_id=callback.from_user.id,
                username=callback.from_user.username,
            )
        )
    except (ClientInviteNotFoundException, ClientAlreadyHasTelegramException):
        await callback.answer(INVALID_CLIENT_INVITE_TEXT, show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return
    except ClientAlreadyExistsException:
        await callback.answer(
            "У вас уже есть профиль клиента в боте — попросите тренера объединить записи.",
            show_alert=True,
        )
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    await callback.answer("Готово!")
    await callback.message.edit_text("✅ Профиль привязан — добро пожаловать!")
    await _open_client_menu(dialog_manager, client.trainer_id)


async def _start_by_referral(
    message: Message, code: str, dialog_manager: DialogManager, mediator: Mediator
) -> None:
    """Ссылка «пригласить друга»: новый человек регистрируется у тренера
    пригласившего, а тот потом получает бонус."""
    try:
        existing: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=message.from_user.id)
        )
    except ClientNotFoundException:
        existing = None
    if existing is not None:
        await message.answer("ℹ️ Вы уже зарегистрированы — открываю ваше меню.")
        await _open_client_menu(dialog_manager, existing.trainer_id)
        return

    try:
        referrer: Client = await mediator.handle(ResolveReferralCodeRequest(code=code))
    except ClientInviteNotFoundException:
        await message.answer(
            "🚫 Эта ссылка недействительна. Попросите друга прислать её ещё раз."
        )
        return
    if not await mediator.handle(IsTrainerAvailableRequest(trainer_id=referrer.trainer_id)):
        await message.answer(TRAINER_UNAVAILABLE_TEXT)
        return
    await dialog_manager.start(
        state=ClientRegisterSG.welcome,
        data={"trainer_id": referrer.trainer_id, "referred_by_client_id": referrer.id},
        mode=StartMode.RESET_STACK,
    )


@router.message(CommandStart(deep_link=True))
@inject
async def process_start_with_token(
    message: Message,
    command: CommandObject,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    token = command.args

    if token.startswith(REFERRAL_PREFIX):
        await _start_by_referral(message, token.removeprefix(REFERRAL_PREFIX), dialog_manager, mediator)
        return

    if token.startswith(CLIENT_INVITE_PREFIX):
        try:
            existing: Client = await mediator.handle(
                GetClientByTgIdRequest(tg_id=message.from_user.id)
            )
        except ClientNotFoundException:
            await _offer_client_claim(message, token.removeprefix(CLIENT_INVITE_PREFIX), mediator)
            return
        await message.answer("ℹ️ Вы уже зарегистрированы — открываю ваше меню.")
        await _open_client_menu(dialog_manager, existing.trainer_id)
        return

    try:
        link: TrainerInviteLink = await mediator.handle(
            ResolveInviteLinkRequest(token=token)
        )
    except (TrainerInviteLinkNotFoundException, TrainerInviteLinkInactiveException):
        await message.answer(
            "🚫 Эта ссылка недействительна или устарела.\n"
            "Доступ к боту возможен только по актуальной ссылке от тренера."
        )
        return

    try:
        client: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=message.from_user.id)
        )
    except ClientNotFoundException:
        if not await mediator.handle(IsTrainerAvailableRequest(trainer_id=link.trainer_id)):
            await message.answer(TRAINER_UNAVAILABLE_TEXT)
            return
        await dialog_manager.start(
            state=ClientRegisterSG.welcome,
            data={"trainer_id": link.trainer_id},
            mode=StartMode.RESET_STACK,
        )
        return

    # клиент уже привязан к тренеру — чужая ссылка его не перепривязывает,
    # он возвращается в меню своего тренера
    if client.trainer_id != link.trainer_id:
        await message.answer(
            "ℹ️ Вы уже зарегистрированы у другого тренера — открываю ваше меню."
        )
    if not await mediator.handle(IsTrainerAvailableRequest(trainer_id=client.trainer_id)):
        await message.answer(TRAINER_UNAVAILABLE_TEXT)
        return

    await dialog_manager.start(
        state=ClientMenuSG.main,
        data={"trainer_id": client.trainer_id},
        mode=StartMode.RESET_STACK,
    )


@router.message(CommandStart(deep_link=False))
@inject
async def process_start_plain(
    message: Message,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        client: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=message.from_user.id)
        )
    except ClientNotFoundException:
        await message.answer(
            "🚫 Доступ к боту возможен только по персональной ссылке от тренера.\n"
            "Попроси тренера отправить тебе ссылку для регистрации."
        )
        return

    if not await mediator.handle(IsTrainerAvailableRequest(trainer_id=client.trainer_id)):
        await message.answer(TRAINER_UNAVAILABLE_TEXT)
        return

    await dialog_manager.start(
        state=ClientMenuSG.main,
        data={"trainer_id": client.trainer_id},
        mode=StartMode.RESET_STACK,
    )
