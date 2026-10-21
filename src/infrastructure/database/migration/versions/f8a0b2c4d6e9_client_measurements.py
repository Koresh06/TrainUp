"""client progress diary (measurements)

Revision ID: f8a0b2c4d6e9
Revises: e5f7a9b1c3d4
Create Date: 2026-10-21 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f8a0b2c4d6e9'
down_revision: Union[str, Sequence[str], None] = 'e5f7a9b1c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # тип bookingactor уже создан миграцией a7b9d1e3f5c4
    booking_actor = postgresql.ENUM('TRAINER', 'CLIENT', 'SYSTEM', name='bookingactor', create_type=False)
    op.create_table(
        'client_measurements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('measured_on', sa.Date(), nullable=False),
        sa.Column('weight', sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column('waist', sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column('chest', sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column('hips', sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column('photo_file_id', sa.VARCHAR(length=255), nullable=True),
        sa.Column('added_by', booking_actor, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='client_measurements_client_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='client_measurements_trainer_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__client_measurements')),
    )
    op.create_index(op.f('ix__client_measurements_client_id'), 'client_measurements', ['client_id'], unique=False)
    op.create_index(op.f('ix__client_measurements_trainer_id'), 'client_measurements', ['trainer_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix__client_measurements_trainer_id'), table_name='client_measurements')
    op.drop_index(op.f('ix__client_measurements_client_id'), table_name='client_measurements')
    op.drop_table('client_measurements')
