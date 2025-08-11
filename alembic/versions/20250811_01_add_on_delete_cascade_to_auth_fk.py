"""add on delete cascade to auth.user_id fk

Revision ID: 20250811_01
Revises: 
Create Date: 2025-08-11 07:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250811_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing foreign key if exists and recreate with ON DELETE CASCADE
    conn = op.get_bind()

    # reflect constraints for auth table
    inspector = sa.inspect(conn)
    fks = inspector.get_foreign_keys('auth')
    for fk in fks:
        if fk['referred_table'] == 'users' and 'user_id' in fk['constrained_columns']:
            op.drop_constraint(fk['name'], 'auth', type_='foreignkey')
            break

    op.create_foreign_key(
        constraint_name=op.f('fk_auth_user_id_users'),
        source_table='auth',
        referent_table='users',
        local_cols=['user_id'],
        remote_cols=['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    # Drop the CASCADE FK and recreate without ON DELETE
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    fks = inspector.get_foreign_keys('auth')
    for fk in fks:
        if fk['referred_table'] == 'users' and 'user_id' in fk['constrained_columns']:
            op.drop_constraint(fk['name'], 'auth', type_='foreignkey')
            break

    op.create_foreign_key(
        constraint_name=op.f('fk_auth_user_id_users'),
        source_table='auth',
        referent_table='users',
        local_cols=['user_id'],
        remote_cols=['id'],
    )
