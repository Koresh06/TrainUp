"""trainer referral program: referral code, referrer, reward date; REFERRAL subscription source

Revision ID: d7f9b1c3e5a8
Revises: c6e8a0b2d4f7
Create Date: 2026-10-22 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7f9b1c3e5a8'
down_revision: Union[str, Sequence[str], None] = 'c6e8a0b2d4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE subscriptionsource ADD VALUE IF NOT EXISTS 'REFERRAL'")
    op.add_column('trainers', sa.Column('referral_code', sa.VARCHAR(length=32), nullable=True))
    op.add_column('trainers', sa.Column('referred_by_trainer_id', sa.Integer(), nullable=True))
    op.add_column('trainers', sa.Column('referral_rewarded_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix__trainers_referral_code'), 'trainers', ['referral_code'], unique=True)
    op.create_index(op.f('ix__trainers_referred_by_trainer_id'), 'trainers', ['referred_by_trainer_id'], unique=False)
    op.create_foreign_key(
        'trainers_referred_by_trainer_id_fkey', 'trainers', 'trainers',
        ['referred_by_trainer_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('trainers_referred_by_trainer_id_fkey', 'trainers', type_='foreignkey')
    op.drop_index(op.f('ix__trainers_referred_by_trainer_id'), table_name='trainers')
    op.drop_index(op.f('ix__trainers_referral_code'), table_name='trainers')
    op.drop_column('trainers', 'referral_rewarded_at')
    op.drop_column('trainers', 'referred_by_trainer_id')
    op.drop_column('trainers', 'referral_code')
    # значение enum не удалить — бонусные подписки становятся «бесплатными»
    op.execute(
        "UPDATE trainer_subscriptions SET source = 'TRIAL' WHERE source::text = 'REFERRAL'"
    )
