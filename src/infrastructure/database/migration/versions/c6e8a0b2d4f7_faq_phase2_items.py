"""FAQ: new items about phase-2 features for already seeded databases

Revision ID: c6e8a0b2d4f7
Revises: b4d6f8a0c2e5
Create Date: 2026-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6e8a0b2d4f7'
down_revision: Union[str, Sequence[str], None] = 'b4d6f8a0c2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# тексты зафиксированы здесь, а не импортом из seed.py: миграция не должна
# меняться, если seed потом отредактируют
NEW_ITEMS = (
    ("TRAINER", (
        ('Клиент без Telegram',
         '👥 Мои клиенты → «➕ Добавить клиента без Telegram»: имя, телефон, заметка. Записывайте его из карточки или в «📅 Расписание → ➕ Записать клиента». Бот ему ничего не пишет — предупреждайте сами. «🔗 Пригласить в бота» — персональная ссылка: откроет её — карточка станет его аккаунтом с историей.'),
        ('Утренняя сводка',
         'Каждое утро (по умолчанию в 8:00) бот присылает вам в личку тренировки на день с заметками о клиентах. Время, вечернюю сводку «на завтра» и дни без тренировок — ⚙️ Настройки → 🔔 Напоминания и сводки.'),
        ('Абонементы и оплаты',
         'Карточка клиента → 🎫 Абонементы → ➕: занятия, цена, срок, оплачен ли. Занятие списывается само после тренировки (и при неявке — отключается в ⚙️ Настройки → 📅 Запись). Неоплаченные разовые — «💵 Оплаты» в карточке, все долги — «💵 Должники» в списке клиентов.'),
        ('Отпуск или больничный',
         '⚙️ Настройки → 🚫 Блокировка → 🏖 Отпуск / больничный: первый и последний день. Слоты закроются, записи отменятся, клиенты получат сообщение. Вышли раньше — удалите период, слоты снова откроются.'),
        ('Явка, неявка и оценки',
         'Накануне бот спрашивает клиента «придёте?»: 👍 в расписании — подтвердил, «Не смогу» отменяет запись. Не пришёл — откройте запись → «🚫 Не пришёл». После тренировки клиент ставит 1–5 ⭐, низкую оценку пришлём вам.'),
        ('Как вернуть пропавших клиентов?',
         '👥 Мои клиенты → «😴 Давно не были»: кто не ходил 3+ недели и никуда не записан. В карточке — «📣 Позвать на тренировку».'),
        ('Дневник прогресса',
         'Карточка клиента → 📈 Прогресс: вес и обхваты одним сообщением (<code>72.5 80 95 98</code>), фото «до/после», графики. Клиент может вести его и сам — «📈 Мой прогресс».'),
        ('Реферальная программа',
         'Клиенты зовут друзей через «🎁 Пригласить друга». Когда друг сходит на первую тренировку, пригласивший получает бесплатные занятия — сколько, задаёте в ⚙️ Настройки → 📅 Запись (по умолчанию выключено).'),
    )),
    ("CLIENT", (
        ('Сколько занятий осталось в абонементе?',
         'Откройте «📝 Моя анкета» — там остаток занятий и срок действия абонемента.'),
        ('Как пригласить друга?',
         '«🎁 Пригласить друга» в меню — отправьте другу ссылку. Если тренер включил бонус, после первой тренировки друга вы получите бесплатные занятия.'),
    )),
)


def upgrade() -> None:
    """Upgrade schema."""
    # FAQ сидится один раз при старте, если пуст; в существующей базе админы
    # могли его править — дописываем только отсутствующие вопросы в конец
    bind = op.get_bind()
    for audience, items in NEW_ITEMS:
        seeded = bind.execute(
            sa.text("SELECT count(*) FROM faq_items WHERE audience = :a"), {"a": audience}
        ).scalar()
        if not seeded:
            continue
        order = bind.execute(
            sa.text("SELECT coalesce(max(\"order\"), 0) FROM faq_items WHERE audience = :a"),
            {"a": audience},
        ).scalar()
        for question, answer in items:
            exists = bind.execute(
                sa.text("SELECT 1 FROM faq_items WHERE audience = :a AND question = :q"),
                {"a": audience, "q": question},
            ).first()
            if exists:
                continue
            order += 1
            bind.execute(
                sa.text(
                    "INSERT INTO faq_items (question, answer, \"order\", is_active, audience) "
                    "VALUES (:q, :ans, :o, true, :a)"
                ),
                {"q": question, "ans": answer, "o": order, "a": audience},
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    for audience, items in NEW_ITEMS:
        for question, _ in items:
            bind.execute(
                sa.text("DELETE FROM faq_items WHERE audience = :a AND question = :q"),
                {"a": audience, "q": question},
            )
