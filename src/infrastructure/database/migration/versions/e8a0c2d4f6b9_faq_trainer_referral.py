"""FAQ: item about the trainer referral program for already seeded databases

Revision ID: e8a0c2d4f6b9
Revises: d7f9b1c3e5a8
Create Date: 2026-10-22 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8a0c2d4f6b9'
down_revision: Union[str, Sequence[str], None] = 'd7f9b1c3e5a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# текст зафиксирован здесь — миграция не должна меняться вместе с seed.py
QUESTION = 'Как пригласить другого тренера?'
ANSWER = (
    '«🎁 Пригласить тренера» в кабинете — ваша ссылка для коллег. По ней тренер '
    'получает пробный период длиннее обычного, а вы — бесплатные дни подписки, '
    'когда он впервые оплатит подписку. Бонус за каждого, без ограничений.'
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    seeded = bind.execute(sa.text("SELECT count(*) FROM faq_items WHERE audience = 'TRAINER'")).scalar()
    exists = bind.execute(
        sa.text("SELECT 1 FROM faq_items WHERE audience = 'TRAINER' AND question = :q"), {"q": QUESTION}
    ).first()
    if not seeded or exists:
        return
    order = bind.execute(
        sa.text("SELECT coalesce(max(\"order\"), 0) FROM faq_items WHERE audience = 'TRAINER'")
    ).scalar()
    bind.execute(
        sa.text(
            "INSERT INTO faq_items (question, answer, \"order\", is_active, audience) "
            "VALUES (:q, :a, :o, true, 'TRAINER')"
        ),
        {"q": QUESTION, "a": ANSWER, "o": order + 1},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.get_bind().execute(
        sa.text("DELETE FROM faq_items WHERE audience = 'TRAINER' AND question = :q"), {"q": QUESTION}
    )
