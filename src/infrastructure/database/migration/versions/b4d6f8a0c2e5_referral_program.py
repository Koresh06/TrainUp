"""referral program: client referral code, referrer, reward date; bonus setting

Revision ID: b4d6f8a0c2e5
Revises: a1c3e5f7b9d0
Create Date: 2026-10-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4d6f8a0c2e5'
down_revision: Union[str, Sequence[str], None] = 'a1c3e5f7b9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('clients', sa.Column('referral_code', sa.VARCHAR(length=32), nullable=True))
    op.add_column('clients', sa.Column('referred_by_client_id', sa.Integer(), nullable=True))
    op.add_column('clients', sa.Column('referral_rewarded_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix__clients_referral_code'), 'clients', ['referral_code'], unique=True)
    op.create_index(op.f('ix__clients_referred_by_client_id'), 'clients', ['referred_by_client_id'], unique=False)
    op.create_foreign_key(
        'clients_referred_by_client_id_fkey', 'clients', 'clients',
        ['referred_by_client_id'], ['id'], ondelete='SET NULL',
    )
    op.add_column(
        'trainer_booking_settings',
        sa.Column('referral_bonus_sessions', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('trainer_booking_settings', 'referral_bonus_sessions')
    op.drop_constraint('clients_referred_by_client_id_fkey', 'clients', type_='foreignkey')
    op.drop_index(op.f('ix__clients_referred_by_client_id'), table_name='clients')
    op.drop_index(op.f('ix__clients_referral_code'), table_name='clients')
    op.drop_column('clients', 'referral_rewarded_at')
    op.drop_column('clients', 'referred_by_client_id')
    op.drop_column('clients', 'referral_code')
