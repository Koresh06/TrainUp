from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Column,
    Group,
    ScrollingGroup,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.link_preview import LinkPreview

from src.presentation.telegram.features.admin.common import on_admin_period_selected
from src.presentation.telegram.features.admin.states import AdminTrainersSG
from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.features.trainer.stats.helper import period_row

from .getters import (
    admin_grant_confirm_getter,
    admin_grant_days_getter,
    admin_grant_plans_getter,
    admin_trainer_card_getter,
    admin_trainer_name_getter,
    admin_trainers_list_getter,
)
from .handlers import (
    on_grant_confirm,
    on_grant_days_entered,
    on_grant_days_selected,
    on_grant_plan_selected,
    on_mail_trainer_clients,
    on_toggle_block_confirm,
    on_trainer_selected,
    validate_grant_days,
)

admin_trainers_dialog = Dialog(
    Window(
        Format(
            "👨‍🏫 <b>Тренеры</b>\n"
            "✅ подписка активна · ⌛ нет подписки · ⛔ заблокирован{empty_hint}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="admin_trainers_select",
                item_id_getter=lambda item: item["id"],
                items="trainers",
                on_click=on_trainer_selected,
            ),
            id="admin_trainers_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminTrainersSG.list,
        getter=admin_trainers_list_getter,
    ),
    Window(
        Format("{card_text}"),
        period_row(on_admin_period_selected),
        Column(
            SwitchTo(Const("🎁 Выдать подписку"), id="to_grant", state=AdminTrainersSG.grant_type),
            Button(
                Const("📢 Рассылка его клиентам"),
                id="mail_clients",
                on_click=on_mail_trainer_clients,
            ),
            SwitchTo(
                Const("⛔ Заблокировать"),
                id="to_block",
                state=AdminTrainersSG.block_confirm,
                style=Style(style=ButtonStyle.DANGER),
                when="is_active",
            ),
            SwitchTo(
                Const("✅ Разблокировать"),
                id="to_unblock",
                state=AdminTrainersSG.block_confirm,
                style=Style(style=ButtonStyle.SUCCESS),
                when="is_blocked",
            ),
        ),
        SwitchTo(Const("⬅️ К списку"), id="back_to_list", state=AdminTrainersSG.list),
        LinkPreview(is_disabled=True),
        state=AdminTrainersSG.card,
        getter=admin_trainer_card_getter,
    ),
    Window(
        Const(
            "🎁 <b>Выдать подписку</b>\n\n"
            "Срок добавится к текущей подписке, если она ещё действует."
        ),
        Column(
            SwitchTo(
                Const("💵 Оплатил наличными/переводом (по тарифу)"),
                id="grant_cash",
                state=AdminTrainersSG.grant_plan,
            ),
            SwitchTo(
                Const("🎁 Бесплатный / пробный период"),
                id="grant_trial",
                state=AdminTrainersSG.grant_days,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_card", state=AdminTrainersSG.card),
        state=AdminTrainersSG.grant_type,
    ),
    Window(
        Const("💵 Выберите оплаченный тариф — сумма попадёт в статистику оплат:"),
        Column(
            Select(
                Format("{item[label]}"),
                id="admin_grant_plan_select",
                item_id_getter=lambda item: item["id"],
                items="plans",
                on_click=on_grant_plan_selected,
            ),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_type", state=AdminTrainersSG.grant_type),
        state=AdminTrainersSG.grant_plan,
        getter=admin_grant_plans_getter,
    ),
    Window(
        Const("🎁 На сколько дней? Выберите или отправьте число:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="admin_grant_days_select",
                item_id_getter=lambda item: item["id"],
                items="days",
                on_click=on_grant_days_selected,
            ),
            width=5,
        ),
        TextInput(
            id="grant_days_input",
            type_factory=validate_grant_days,
            on_success=on_grant_days_entered,
            on_error=on_input_error,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_type", state=AdminTrainersSG.grant_type),
        state=AdminTrainersSG.grant_days,
        getter=admin_grant_days_getter,
    ),
    Window(
        Format("Выдать подписку тренеру <b>{trainer_name}</b>?\n\n{grant_summary}"),
        Button(
            Const("✅ Выдать"),
            id="grant_confirm",
            on_click=on_grant_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_type", state=AdminTrainersSG.grant_type),
        state=AdminTrainersSG.grant_confirm,
        getter=admin_grant_confirm_getter,
    ),
    Window(
        Format(
            "Изменить доступ тренера <b>{trainer_name}</b>?\n\n"
            "Блокировка закрывает ему кабинет, а его клиентам — запись и заявки."
        ),
        Button(Const("✅ Подтвердить"), id="block_confirm", on_click=on_toggle_block_confirm),
        SwitchTo(Const("⬅️ Назад"), id="back_to_card", state=AdminTrainersSG.card),
        state=AdminTrainersSG.block_confirm,
        getter=admin_trainer_name_getter,
    ),
)
