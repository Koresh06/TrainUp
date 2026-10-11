from enum import Enum


class MailingTarget(str, Enum):
    ALL_TRAINERS = "trainers"
    ALL_CLIENTS = "clients"
    EVERYONE = "everyone"
    TRAINER_CLIENTS = "trainer_clients"  # клиенты конкретного тренера

    def label(self) -> str:
        match self:
            case MailingTarget.ALL_TRAINERS:
                return "👨‍🏫 Всем тренерам"
            case MailingTarget.ALL_CLIENTS:
                return "👥 Всем клиентам"
            case MailingTarget.EVERYONE:
                return "📢 Всем пользователям"
            case MailingTarget.TRAINER_CLIENTS:
                return "🎯 Клиентам тренера"
