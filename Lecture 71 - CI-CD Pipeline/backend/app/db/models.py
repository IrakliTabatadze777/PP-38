from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))

    orders: Mapped[list[Order]] = relationship(back_populates="customer")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price_cents >= 0", name="products_price_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    category: Mapped[str] = mapped_column(String(50))
    price_cents: Mapped[int] = mapped_column(Integer)
    final_sale: Mapped[bool] = mapped_column(Boolean, default=False)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('placed', 'shipped', 'delivered', 'cancelled')", name="orders_status_valid"
        ),
        CheckConstraint("shipping_cents >= 0", name="orders_shipping_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipping_cents: Mapped[int] = mapped_column(Integer)

    customer: Mapped[Customer] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order", order_by="OrderItem.id")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("price_paid_cents >= 0", name="order_items_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    price_paid_cents: Mapped[int] = mapped_column(Integer)
    refunded: Mapped[bool] = mapped_column(Boolean, default=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()
    refund: Mapped[Refund | None] = relationship(back_populates="order_item")


class Conversation(Base):
    __tablename__ = "conversations"

    thread_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(60))
    customer_email: Mapped[str | None] = mapped_column(String(254), index=True)
    created_at: Mapped[datetime] = _now_column()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('customer', 'reviewer', 'admin')", name="users_role_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = _now_column()


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[str] = mapped_column(String(32), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _now_column()


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        UniqueConstraint("thread_id", "tool_call_id", name="approvals_thread_tool_call_key"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'edited', 'rejected')", name="approvals_status_valid"
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    tool_call_id: Mapped[str] = mapped_column(String(100))
    tool: Mapped[str] = mapped_column(String(50))
    args_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewer_id: Mapped[str | None] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _now_column()
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (CheckConstraint("amount_cents >= 0", name="refunds_amount_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), unique=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    include_shipping: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(String(50))
    approval_id: Mapped[str | None] = mapped_column(ForeignKey("approvals.id"))
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = _now_column()

    order_item: Mapped[OrderItem] = relationship(back_populates="refund")


class Replacement(Base):
    __tablename__ = "replacements"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    reason: Mapped[str] = mapped_column(String(50))
    approval_id: Mapped[str | None] = mapped_column(ForeignKey("approvals.id"))
    created_at: Mapped[datetime] = _now_column()


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("priority IN ('normal', 'high')", name="tickets_priority_valid"),
        CheckConstraint("status IN ('open', 'closed')", name="tickets_status_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    summary: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10), default="normal")
    status: Mapped[str] = mapped_column(String(10), default="open")
    created_at: Mapped[datetime] = _now_column()
