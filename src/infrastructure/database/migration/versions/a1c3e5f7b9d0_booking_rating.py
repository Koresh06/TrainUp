"""booking rating by client and trainer setting

Revision ID: a1c3e5f7b9d0
Revises: f8a0b2c4d6e9
Create Date: 2026-10-22 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3e5f7b9d0'
down_revision: Union[str, Sequence[str], None] = 'f8a0b2c4d6e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('rating', sa.Integer(), nullable=True))
    op.add_column(
        'trainer_booking_settings',
        sa.Column('ask_rating', sa.Boolean(), server_default='true', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('trainer_booking_settings', 'ask_rating')
    op.drop_column('bookings', 'rating')
