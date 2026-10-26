from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Customer, Order, OrderItem, Product, Refund
from scripts.seed import CUSTOMER_EMAIL, seed, truncate_all


async def _order(session: AsyncSession, number: str) -> Order:
    return await session.scalar(
        select(Order)
        .where(Order.order_number == number)
        .options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.refund),
        )
    )


@pytest.fixture
async def seeded(db_session: AsyncSession) -> tuple[AsyncSession, datetime]:
    now = datetime.now(UTC)
    await seed(db_session, now=now)
    await db_session.commit()
    return db_session, now


async def test_order_1042_is_a_jacket_delivered_three_days_ago(seeded) -> None:
    session, now = seeded
    order = await _order(session, "1042")

    assert order.customer.email == CUSTOMER_EMAIL
    assert order.status == "delivered"
    assert (now - order.delivered_at).days == 3
    assert order.shipping_cents == 950
    [item] = order.items
    assert item.product.name == "Alpine Shell Jacket"
    assert item.product.category == "jackets"
    assert item.price_paid_cents == 8900


SCENARIOS = {
    "1042": ("Alpine Shell Jacket", 8900, "delivered", 3, False, False),
    "1043": ("Trail Boots", 14000, "delivered", 33, False, False),
    "1044": ("Two-Person Tent", 24900, "delivered", 60, False, False),
    "1045": ("Wool Gloves", 2400, "delivered", 5, True, False),
    "1046": ("Daypack", 6500, "delivered", 10, False, True),
    "1047": ("Fleece Pullover", 7500, "shipped", None, False, False),
    "1049": ("Expedition Tent", 28900, "delivered", 2, False, False),
}


@pytest.mark.parametrize("number", SCENARIOS)
async def test_scenario_orders(seeded, number: str) -> None:
    session, now = seeded
    product, paid, status, days, final_sale, refunded = SCENARIOS[number]
    order = await _order(session, number)

    assert order.customer.email == CUSTOMER_EMAIL
    assert order.status == status
    if days is None:
        assert order.delivered_at is None
    else:
        assert (now - order.delivered_at).days == days
    [item] = order.items
    assert item.product.name == product
    assert item.price_paid_cents == paid
    assert item.product.final_sale is final_sale
    assert item.refunded is refunded
    assert (item.refund is not None) is refunded


async def test_seed_volume(seeded) -> None:
    session, _ = seeded

    def count(model):
        return session.scalar(select(func.count()).select_from(model))

    assert 30 <= await count(Product) <= 40
    assert await count(Customer) == 50
    assert await count(Order) >= 200
    assert await _order(session, "1048") is None


async def test_seed_is_deterministic(db_session: AsyncSession) -> None:
    now = datetime.now(UTC)

    async def snapshot() -> list[tuple]:
        await truncate_all(db_session)
        await seed(db_session, now=now)
        await db_session.commit()
        rows = await db_session.execute(
            select(Order.order_number, Customer.email, Order.status, OrderItem.price_paid_cents)
            .join(Customer, Customer.id == Order.customer_id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .order_by(Order.order_number, OrderItem.id)
        )
        return [tuple(row) for row in rows]

    assert await snapshot() == await snapshot()


async def test_second_refund_for_same_item_is_rejected_by_the_database(seeded) -> None:
    session, _ = seeded
    order = await _order(session, "1046")
    session.add(
        Refund(
            order_item_id=order.items[0].id,
            amount_cents=100,
            reason="other",
            idempotency_key="another-key",
        )
    )

    with pytest.raises(IntegrityError):
        await session.flush()
    await session.rollback()
