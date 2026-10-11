from enum import Enum


class FaqAudience(str, Enum):
    CLIENT = "client"    # «✉️ Обратная связь → ❓ Частые вопросы» у клиентов
    TRAINER = "trainer"  # «❓ Помощь» в кабинете тренера — правила пользования ботом
