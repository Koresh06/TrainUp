from enum import Enum


class AdminPermission(str, Enum):
    """Права обычного админа. Супер-админ (ADMIN_IDS в .env) может всё,
    включая управление админами — это право никому не выдаётся."""

    STATS = "stats"
    PAYMENTS = "payments"
    TRAINERS_APPROVE = "trainers_approve"
    TRAINERS_VIEW = "trainers_view"
    TRAINERS_MANAGE = "trainers_manage"
    CLIENTS_VIEW = "clients_view"
    CLIENTS_MANAGE = "clients_manage"
    MAILING = "mailing"
    FAQ = "faq"
    EXPORTS = "exports"

    def label(self) -> str:
        return ADMIN_PERMISSION_LABELS[self]


ADMIN_PERMISSION_LABELS: dict[AdminPermission, str] = {
    AdminPermission.STATS: "📊 Статистика",
    AdminPermission.PAYMENTS: "💳 Подтверждение оплат",
    AdminPermission.TRAINERS_APPROVE: "🛂 Подтверждение новых тренеров",
    AdminPermission.TRAINERS_VIEW: "👨‍🏫 Просмотр тренеров",
    AdminPermission.TRAINERS_MANAGE: "🎁 Подписки и блокировка тренеров",
    AdminPermission.CLIENTS_VIEW: "👥 Просмотр клиентов",
    AdminPermission.CLIENTS_MANAGE: "⛔ Блокировка клиентов",
    AdminPermission.MAILING: "📢 Рассылки",
    AdminPermission.FAQ: "❓ FAQ",
    AdminPermission.EXPORTS: "📥 Выгрузки (телефоны и анкеты)",
}


class AdminNotification(str, Enum):
    """Что бот шлёт админам. Каждый тип можно выключить себе в «🔔 Уведомления»."""

    MANUAL_PAYMENT = "manual_payment"
    TRAINER_APPLICATION = "trainer_application"
    PAYMENT_PAID = "payment_paid"
    MAILING_REPORT = "mailing_report"

    def label(self) -> str:
        return ADMIN_NOTIFICATION_LABELS[self]

    @property
    def required_permission(self) -> AdminPermission:
        return ADMIN_NOTIFICATION_PERMISSIONS[self]


ADMIN_NOTIFICATION_LABELS: dict[AdminNotification, str] = {
    AdminNotification.MANUAL_PAYMENT: "🤝 Заявки на ручную оплату",
    AdminNotification.TRAINER_APPLICATION: "🛂 Заявки новых тренеров",
    AdminNotification.PAYMENT_PAID: "💸 Успешные оплаты",
    AdminNotification.MAILING_REPORT: "📢 Отчёты о рассылках",
}

ADMIN_NOTIFICATION_PERMISSIONS: dict[AdminNotification, AdminPermission] = {
    AdminNotification.MANUAL_PAYMENT: AdminPermission.PAYMENTS,
    AdminNotification.TRAINER_APPLICATION: AdminPermission.TRAINERS_APPROVE,
    AdminNotification.PAYMENT_PAID: AdminPermission.PAYMENTS,
    AdminNotification.MAILING_REPORT: AdminPermission.MAILING,
}
