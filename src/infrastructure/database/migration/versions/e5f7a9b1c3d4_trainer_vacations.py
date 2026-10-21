"""trainer vacations

Revision ID: e5f7a9b1c3d4
Revises: d2e4f6a8c0b1
Create Date: 2026-10-21 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f7a9b1c3d4'
down_revision: Union[str, Sequence[str], None] = 'd2e4f6a8c0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'trainer_vacations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('note', sa.VARCHAR(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='trainer_vacations_trainer_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__trainer_vacations')),
    )
    op.create_index(op.f('ix__trainer_vacations_trainer_id'), 'trainer_vacations', ['trainer_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix__trainer_vacations_trainer_id'), table_name='trainer_vacations')
    op.drop_table('trainer_vacations')
