"""drop trainer-side payment tracking (bookings/client_packages paid_at)

Revision ID: d0f2a4b6c8e1
Revises: c8e0a2b4d6f1
Create Date: 2026-11-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0f2a4b6c8e1'
down_revision: Union[str, Sequence[str], None] = 'c8e0a2b4d6f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# тексты зафиксированы здесь, а не импортом из seed.py
OLD_QUESTION = 'Абонементы и оплаты'
OLD_ANSWER = (
    'Карточка клиента → 🎫 Абонементы → ➕: занятия, цена, срок, оплачен ли. Занятие '
    'списывается само после тренировки (и при неявке — отключается в ⚙️ Настройки → '
    '📅 Запись). Неоплаченные разовые — «💵 Оплаты» в карточке, все долги — '
    '«💵 Должники» в списке клиентов.'
)
NEW_QUESTION = 'Абонементы'
NEW_ANSWER = (
    'Карточка клиента → 🎫 Абонементы → ➕: занятия, цена, срок. Занятие списывается '
    'само после тренировки (и при неявке — отключается в ⚙️ Настройки → 📅 Запись). '
    'Оплаты бот не отслеживает: тренировка, которая прошла и не была отменена, сама '
    'засчитывается в статистику и доход.'
)


def _swap_faq(from_q: str, from_a: str, to_q: str, to_a: str) -> None:
    # правим только нетронутый ответ: если админ уже переписал его, не затираем
    op.get_bind().execute(
        sa.text(
            "UPDATE faq_items SET question = :to_q, answer = :to_a "
            "WHERE audience = 'TRAINER' AND question = :from_q AND answer = :from_a"
        ),
        {"from_q": from_q, "from_a": from_a, "to_q": to_q, "to_a": to_a},
    )


def upgrade() -> None:
    """Upgrade schema."""
    # тренер больше не отмечает оплаты: прошедшая неотменённая тренировка
    # сама считается проведённой, «Должников» и «Оплат» нет
    op.drop_column('bookings', 'paid_at')
    op.drop_column('client_packages', 'paid_at')
    _swap_faq(OLD_QUESTION, OLD_ANSWER, NEW_QUESTION, NEW_ANSWER)


def downgrade() -> None:
    """Downgrade schema."""
    _swap_faq(NEW_QUESTION, NEW_ANSWER, OLD_QUESTION, OLD_ANSWER)
    op.add_column(
        'client_packages',
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'bookings',
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    )
