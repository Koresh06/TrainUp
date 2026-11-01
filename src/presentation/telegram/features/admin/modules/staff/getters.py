from html import escape

from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.staff.get_admins import GetAdminRequest, GetAdminsRequest
from src.domain.entities.bot_admin import BotAdmin
from src.domain.enums.admin import AdminPermission


@inject
async def admins_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    admins: list[BotAdmin] = await mediator.handle(GetAdminsRequest())
    return {
        "admins": [
            {"id": admin.tg_id, "label": f"{admin.title} · прав: {len(admin.permissions)}"}
            for admin in admins
        ],
        "empty_hint": "" if admins else "\n\nПока никого нет — добавьте первого.",
    }


@inject
async def admin_card_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    admin: BotAdmin = await mediator.handle(
        GetAdminRequest(tg_id=dialog_manager.dialog_data["admin_tg_id"])
    )
    return {
        "card_text": (
            f"👮 <b>{escape(admin.title)}</b>\n"
            f"🆔 <code>{admin.tg_id}</code>\n\n"
            f"Нажмите на право, чтобы выдать или забрать его. "
            f"Изменения работают сразу."
        ),
        "permissions": [
            {
                "id": permission.value,
                "label": f"{'✅' if permission in admin.permissions else '⬜️'} "
                f"{permission.label()}",
            }
            for permission in AdminPermission
        ],
    }
