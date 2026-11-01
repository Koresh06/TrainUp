"""bot admins with permissions

Revision ID: a9c1e3f5b7d2
Revises: e8a0c2d4f6b9
Create Date: 2026-11-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9c1e3f5b7d2'
down_revision: Union[str, Sequence[str], None] = 'e8a0c2d4f6b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'bot_admins',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=True),
        sa.Column('permissions', sa.ARRAY(sa.VARCHAR(length=32)), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('muted_notifications', sa.ARRAY(sa.VARCHAR(length=32)), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('added_by_tg_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__bot_admins')),
    )
    op.create_index(op.f('ix__bot_admins_tg_id'), 'bot_admins', ['tg_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix__bot_admins_tg_id'), table_name='bot_admins')
    op.drop_table('bot_admins')
