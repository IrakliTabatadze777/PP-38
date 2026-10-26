
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("thread_id", sa.String(length=100), nullable=False),
        sa.Column("tool_call_id", sa.String(length=100), nullable=False),
        sa.Column("tool", sa.String(length=50), nullable=False),
        sa.Column("args_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reviewer_id", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'edited', 'rejected')", name="approvals_status_valid"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", "tool_call_id", name="approvals_thread_tool_call_key"),
    )
    op.create_index(op.f("ix_approvals_thread_id"), "approvals", ["thread_id"], unique=False)
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("final_sale", sa.Boolean(), nullable=False),
        sa.CheckConstraint("price_cents >= 0", name="products_price_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.String(length=100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("priority IN ('normal', 'high')", name="tickets_priority_valid"),
        sa.CheckConstraint("status IN ('open', 'closed')", name="tickets_status_valid"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_thread_id"), "tickets", ["thread_id"], unique=False)
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(length=20), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipping_cents", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "status IN ('placed', 'shipped', 'delivered', 'cancelled')", name="orders_status_valid"
        ),
        sa.CheckConstraint("shipping_cents >= 0", name="orders_shipping_non_negative"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index(op.f("ix_orders_customer_id"), "orders", ["customer_id"], unique=False)
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("price_paid_cents", sa.Integer(), nullable=False),
        sa.Column("refunded", sa.Boolean(), nullable=False),
        sa.CheckConstraint("price_paid_cents >= 0", name="order_items_price_non_negative"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("include_shipping", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=50), nullable=False),
        sa.Column("approval_id", sa.String(length=40), nullable=True),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount_cents >= 0", name="refunds_amount_non_negative"),
        sa.ForeignKeyConstraint(
            ["approval_id"],
            ["approvals.id"],
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint("order_item_id"),
    )
    op.create_table(
        "replacements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=50), nullable=False),
        sa.Column("approval_id", sa.String(length=40), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["approval_id"],
            ["approvals.id"],
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("replacements")
    op.drop_table("refunds")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")
    op.drop_index(op.f("ix_orders_customer_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_tickets_thread_id"), table_name="tickets")
    op.drop_table("tickets")
    op.drop_table("products")
    op.drop_table("customers")
    op.drop_index(op.f("ix_approvals_thread_id"), table_name="approvals")
    op.drop_table("approvals")
