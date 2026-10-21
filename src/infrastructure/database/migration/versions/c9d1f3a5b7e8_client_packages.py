"""client packages (абонементы), booking payment fields, no-show charging setting

Revision ID: c9d1f3a5b7e8
Revises: b3c5e7f9a1d2
Create Date: 2026-10-21 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d1f3a5b7e8'
down_revision: Union[str, Sequence[str], None] = 'b3c5e7f9a1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

package_status = sa.Enum('ACTIVE', 'FINISHED', 'CANCELLED', name='packagestatus')


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'client_packages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.VARCHAR(length=100), nullable=False),
        sa.Column('sessions_total', sa.Integer(), nullable=False),
        sa.Column('sessions_used', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('status', package_status, nullable=False),
        sa.Column('is_bonus', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='client_packages_client_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id'], name='client_packages_trainer_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__client_packages')),
    )
    op.create_index(op.f('ix__client_packages_client_id'), 'client_packages', ['client_id'], unique=False)
    op.create_index(op.f('ix__client_packages_trainer_id'), 'client_packages', ['trainer_id'], unique=False)

    op.add_column('bookings', sa.Column('package_id', sa.Integer(), nullable=True))
    op.add_column('bookings', sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix__bookings_package_id'), 'bookings', ['package_id'], unique=False)
    op.create_foreign_key(
        'bookings_package_id_fkey', 'bookings', 'client_packages', ['package_id'], ['id'], ondelete='SET NULL'
    )

    op.add_column(
        'trainer_booking_settings',
        sa.Column('no_show_charges_package', sa.Boolean(), server_default='true', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('trainer_booking_settings', 'no_show_charges_package')
    op.drop_constraint('bookings_package_id_fkey', 'bookings', type_='foreignkey')
    op.drop_index(op.f('ix__bookings_package_id'), table_name='bookings')
    op.drop_column('bookings', 'paid_at')
    op.drop_column('bookings', 'package_id')
    op.drop_index(op.f('ix__client_packages_trainer_id'), table_name='client_packages')
    op.drop_index(op.f('ix__client_packages_client_id'), table_name='client_packages')
    op.drop_table('client_packages')
    package_status.drop(op.get_bind(), checkfirst=True)
