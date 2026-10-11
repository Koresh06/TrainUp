"""subscription source and notifications, faq audience, «Другое» option

Revision ID: c4e8a1f2d907
Revises: b7d41e09c3a2
Create Date: 2026-10-11 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4e8a1f2d907'
down_revision: Union[str, Sequence[str], None] = 'b7d41e09c3a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


subscription_source = postgresql.ENUM('PURCHASE', 'CASH', 'TRIAL', name='subscriptionsource')
faq_audience = postgresql.ENUM('CLIENT', 'TRAINER', name='faqaudience')


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE subscriptionplan ADD VALUE IF NOT EXISTS 'CUSTOM'")

    subscription_source.create(op.get_bind(), checkfirst=True)
    op.add_column('trainer_subscriptions', sa.Column('source', subscription_source, server_default='PURCHASE', nullable=False))
    op.add_column('trainer_subscriptions', sa.Column('notified_stage', sa.Integer(), server_default='0', nullable=False))

    faq_audience.create(op.get_bind(), checkfirst=True)
    op.add_column('faq_items', sa.Column('audience', faq_audience, server_default='CLIENT', nullable=False))
    op.create_index(op.f('ix__faq_items_audience'), 'faq_items', ['audience'], unique=False)

    # «Другое» во всех вопросах анкеты теперь одинаковое и требует текста
    op.execute(
        """
        UPDATE registration_questions
        SET options = array_replace(options, 'Другое (указать самостоятельно)', 'Другое')
        WHERE 'Другое (указать самостоятельно)' = ANY(options)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix__faq_items_audience'), table_name='faq_items')
    op.drop_column('faq_items', 'audience')
    faq_audience.drop(op.get_bind(), checkfirst=True)
    op.drop_column('trainer_subscriptions', 'notified_stage')
    op.drop_column('trainer_subscriptions', 'source')
    subscription_source.drop(op.get_bind(), checkfirst=True)
    # значение CUSTOM из enum subscriptionplan в Postgres не удаляется
