
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("thread_id", sa.String(length=100), primary_key=True),
        sa.Column("title", sa.String(length=60), nullable=False),
        sa.Column("customer_email", sa.String(length=254)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_conversations_customer_email", "conversations", ["customer_email"])


def downgrade() -> None:
    op.drop_index("ix_conversations_customer_email", table_name="conversations")
    op.drop_table("conversations")
