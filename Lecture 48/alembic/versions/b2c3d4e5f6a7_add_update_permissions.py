"""add update permissions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-12 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UPDATE_PERMISSIONS = [
    (9, 'products:update', 'Update products'),
    (10, 'orders:update', 'Update orders'),
    (11, 'users:update', 'Update users'),
]


def upgrade() -> None:
    permissions_table = sa.table(
        'permissions',
        sa.column('id', sa.Integer),
        sa.column('code', sa.String),
        sa.column('description', sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [
            {'id': permission_id, 'code': code, 'description': description}
            for permission_id, code, description in UPDATE_PERMISSIONS
        ],
    )

    role_permissions_table = sa.table(
        'role_permissions',
        sa.column('id', sa.Integer),
        sa.column('role', sa.Enum),
        sa.column('permission_id', sa.Integer),
    )
    # Existing seed used ids 1..10; continue from 11
    op.bulk_insert(
        role_permissions_table,
        [
            {'id': 11, 'role': 'ADMIN', 'permission_id': 9},
            {'id': 12, 'role': 'ADMIN', 'permission_id': 10},
            {'id': 13, 'role': 'ADMIN', 'permission_id': 11},
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN (9, 10, 11)"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM permissions WHERE code IN "
            "('products:update', 'orders:update', 'users:update')"
        )
    )
