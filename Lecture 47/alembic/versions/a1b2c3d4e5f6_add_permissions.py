"""add permissions and role_permissions

Revision ID: a1b2c3d4e5f6
Revises: 0df0aed557d3
Create Date: 2026-08-12 17:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '0df0aed557d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PERMISSIONS = [
    ('products:create', 'Create products'),
    ('products:delete', 'Delete products'),
    ('orders:read', 'Read orders'),
    ('orders:create', 'Create orders'),
    ('orders:delete', 'Delete orders'),
    ('users:read', 'Read users'),
    ('users:create', 'Create users'),
    ('users:delete', 'Delete users'),
]

ADMIN_PERMISSIONS = [code for code, _ in PERMISSIONS]
CUSTOMER_PERMISSIONS = [
    'orders:read',
    'orders:create',
]


def upgrade() -> None:
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.UniqueConstraint('code'),
    )

    userrole = postgresql.ENUM('ADMIN', 'CUSTOMER', name='userrole', create_type=False)
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('role', userrole, nullable=False),
        sa.Column('permission_id', sa.Integer(), sa.ForeignKey('permissions.id'), nullable=False),
        sa.UniqueConstraint('role', 'permission_id', name='uq_role_permission'),
    )

    permissions_table = sa.table(
        'permissions',
        sa.column('id', sa.Integer),
        sa.column('code', sa.String),
        sa.column('description', sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [
            {'id': index, 'code': code, 'description': description}
            for index, (code, description) in enumerate(PERMISSIONS, start=1)
        ],
    )

    code_to_id = {code: index for index, (code, _) in enumerate(PERMISSIONS, start=1)}
    role_permissions_table = sa.table(
        'role_permissions',
        sa.column('id', sa.Integer),
        sa.column('role', sa.Enum),
        sa.column('permission_id', sa.Integer),
    )

    rows = []
    row_id = 1
    for code in ADMIN_PERMISSIONS:
        rows.append({'id': row_id, 'role': 'ADMIN', 'permission_id': code_to_id[code]})
        row_id += 1
    for code in CUSTOMER_PERMISSIONS:
        rows.append({'id': row_id, 'role': 'CUSTOMER', 'permission_id': code_to_id[code]})
        row_id += 1

    op.bulk_insert(role_permissions_table, rows)


def downgrade() -> None:
    op.drop_table('role_permissions')
    op.drop_table('permissions')
