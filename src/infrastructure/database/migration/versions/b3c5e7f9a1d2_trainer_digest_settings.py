"""trainer digest settings: morning/evening hour, empty days, last sent dates

Revision ID: b3c5e7f9a1d2
Revises: a7b9d1e3f5c4
Create Date: 2026-10-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c5e7f9a1d2'
down_revision: Union[str, Sequence[str], None] = 'a7b9d1e3f5c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # у существующих тренеров утренняя сводка включена — в 8:00, как у новых
    op.add_column(
        'trainer_reminder_settings',
        sa.Column('morning_digest_hour', sa.Integer(), nullable=True, server_default='8'),
    )
    op.alter_column('trainer_reminder_settings', 'morning_digest_hour', server_default=None)
    op.add_column('trainer_reminder_settings', sa.Column('evening_digest_hour', sa.Integer(), nullable=True))
    op.add_column(
        'trainer_reminder_settings',
        sa.Column('digest_on_empty_days', sa.Boolean(), server_default='false', nullable=False),
    )
    op.add_column('trainer_reminder_settings', sa.Column('last_morning_digest_on', sa.Date(), nullable=True))
    op.add_column('trainer_reminder_settings', sa.Column('last_evening_digest_on', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('trainer_reminder_settings', 'last_evening_digest_on')
    op.drop_column('trainer_reminder_settings', 'last_morning_digest_on')
    op.drop_column('trainer_reminder_settings', 'digest_on_empty_days')
    op.drop_column('trainer_reminder_settings', 'evening_digest_hour')
    op.drop_column('trainer_reminder_settings', 'morning_digest_hour')
