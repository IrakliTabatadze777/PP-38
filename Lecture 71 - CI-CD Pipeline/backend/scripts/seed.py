"""Fill the database with fake demo data and the three demo accounts.

Accounts (password for all of them: support-demo):
  customer@example.com  (customer)  owns the demo orders 1042-1049 and the review history
  reviewer@example.com  (reviewer)  decides approval requests
  admin@example.com     (admin)     manages the knowledge base documents
"""

import argparse
import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from faker import Faker
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import settings
from app.db.models import Approval, Customer, Order, OrderItem, Product, Refund, Ticket, User
from app.db.session import create_engine, create_session_factory
from app.security import hash_password

SEED = 42
CUSTOMER_EMAIL = "customer@example.com"
CUSTOMER_NAME = "Maria Lopez"
REVIEWER_EMAIL = "reviewer@example.com"
ADMIN_EMAIL = "admin@example.com"
RANDOM_ORDER_COUNT = 200
CUSTOMER_COUNT = 50
FIRST_RANDOM_ORDER_NUMBER = 2001

TABLES = (
    "refunds, replacements, approvals, tickets, conversations, "
    "order_items, orders, products, customers, refresh_tokens, users"
)

DEMO_PASSWORD = "support-demo"
DEMO_USERS: list[tuple[str, str, str]] = [
    (CUSTOMER_EMAIL, CUSTOMER_NAME, "customer"),
    (REVIEWER_EMAIL, "Riley Reviewer", "reviewer"),
    (ADMIN_EMAIL, "Alex Admin", "admin"),
]

CATALOG: list[tuple[str, str, int, bool]] = [
    ("Alpine Shell Jacket", "jackets", 8900, False),
    ("Ridgeline Rain Jacket", "jackets", 12900, False),
    ("Summit Down Jacket", "jackets", 21900, False),
    ("Trailhead Windbreaker", "jackets", 6900, False),
    ("Glacier Insulated Parka", "jackets", 27900, False),
    ("Last Season Softshell", "jackets", 4900, True),
    ("Trail Boots", "boots", 14000, False),
    ("Ridge Hiking Boots", "boots", 16900, False),
    ("Summit Mountaineering Boots", "boots", 31900, False),
    ("Creekside Trail Shoes", "boots", 9900, False),
    ("Winter Snow Boots", "boots", 18900, False),
    ("Clearance Approach Shoes", "boots", 5900, True),
    ("Two-Person Tent", "tents", 24900, False),
    ("Expedition Tent", "tents", 28900, False),
    ("Solo Ultralight Tent", "tents", 19900, False),
    ("Family Cabin Tent", "tents", 34900, False),
    ("Basecamp Dome Tent", "tents", 26900, False),
    ("Tarp Shelter", "tents", 5900, False),
    ("Daypack", "backpacks", 6500, False),
    ("Overnight Pack 40L", "backpacks", 13900, False),
    ("Expedition Pack 65L", "backpacks", 21900, False),
    ("Summit Lumbar Pack", "backpacks", 3900, False),
    ("Hydration Pack 12L", "backpacks", 8900, False),
    ("Discontinued Rolltop Pack", "backpacks", 4500, True),
    ("Fleece Pullover", "apparel", 7500, False),
    ("Merino Base Layer Top", "apparel", 6900, False),
    ("Merino Base Layer Bottoms", "apparel", 6500, False),
    ("Trail Hiking Pants", "apparel", 7900, False),
    ("Quick-Dry Hiking Shirt", "apparel", 4500, False),
    ("Wool Gloves", "accessories", 2400, True),
    ("Insulated Winter Gloves", "accessories", 4900, False),
    ("Merino Beanie", "accessories", 2800, False),
    ("Trekking Poles", "accessories", 8900, False),
    ("Headlamp 400 Lumen", "accessories", 3900, False),
    ("Insulated Water Bottle", "accessories", 2900, False),
    ("Sleeping Bag 20F", "accessories", 14900, False),
]

SHIPPING_CHOICES = [0, 950, 1200]


def _demo_password_hash() -> str:
    return hash_password(DEMO_PASSWORD)


async def seed_users(session: AsyncSession) -> int:
    existing = set(await session.scalars(select(User.email)))
    added = [
        User(email=email, name=name, role=role, password_hash=_demo_password_hash())
        for email, name, role in DEMO_USERS
        if email not in existing
    ]
    session.add_all(added)
    await session.flush()
    return len(added)


def _utc_now() -> datetime:
    return datetime.now(UTC)


async def seed(session: AsyncSession, now: datetime | None = None) -> None:
    now = now or _utc_now()
    rng = random.Random(SEED)
    fake = Faker()
    Faker.seed(SEED)

    products = {
        name: Product(name=name, category=category, price_cents=price, final_sale=final_sale)
        for name, category, price, final_sale in CATALOG
    }
    session.add_all(products.values())

    demo_customer = Customer(email=CUSTOMER_EMAIL, name=CUSTOMER_NAME)
    others = [
        Customer(email=fake.unique.safe_email(), name=fake.name())
        for _ in range(CUSTOMER_COUNT - 1)
    ]
    session.add_all([demo_customer, *others])
    await session.flush()

    _add_scenario_orders(session, demo_customer, products, now)
    _add_random_orders(session, rng, others, list(products.values()), now)
    await session.flush()


def _add_scenario_orders(
    session: AsyncSession, customer: Customer, products: dict[str, Product], now: datetime
) -> None:
    scenarios = [
        ("1042", "Alpine Shell Jacket", 8900, 950, "delivered", 3),
        ("1043", "Trail Boots", 14000, 950, "delivered", 33),
        ("1044", "Two-Person Tent", 24900, 1200, "delivered", 60),
        ("1045", "Wool Gloves", 2400, 950, "delivered", 5),
        ("1046", "Daypack", 6500, 950, "delivered", 10),
        ("1047", "Fleece Pullover", 7500, 950, "shipped", None),
        ("1049", "Expedition Tent", 28900, 1200, "delivered", 2),
    ]
    for number, product_name, paid, shipping, status, days_ago in scenarios:
        delivered_at = now - timedelta(days=days_ago) if days_ago is not None else None
        placed_at = (delivered_at or now - timedelta(days=2)) - timedelta(days=5)
        item = OrderItem(product=products[product_name], price_paid_cents=paid, refunded=False)
        if number == "1046":
            item.refunded = True
            item.refund = Refund(
                amount_cents=paid,
                include_shipping=False,
                reason="changed_mind",
                idempotency_key="seed-order-1046",
            )
        session.add(
            Order(
                order_number=number,
                customer=customer,
                status=status,
                placed_at=placed_at,
                delivered_at=delivered_at,
                shipping_cents=shipping,
                items=[item],
            )
        )


def _add_random_orders(
    session: AsyncSession,
    rng: random.Random,
    customers: list[Customer],
    products: list[Product],
    now: datetime,
) -> None:
    for index in range(RANDOM_ORDER_COUNT):
        number = str(FIRST_RANDOM_ORDER_NUMBER + index)
        status = rng.choices(
            ["delivered", "shipped", "placed", "cancelled"], weights=[70, 12, 10, 8]
        )[0]
        delivered_at = None
        if status == "delivered":
            delivered_at = now - timedelta(days=rng.randint(1, 120), hours=rng.randint(0, 23))
            placed_at = delivered_at - timedelta(days=rng.randint(3, 8))
        else:
            placed_at = now - timedelta(days=rng.randint(0, 6))

        items = []
        for product in rng.sample(products, k=rng.choice([1, 1, 2, 3])):
            paid = round(product.price_cents * rng.choice([1.0, 1.0, 0.9, 0.8]))
            item = OrderItem(product=product, price_paid_cents=paid, refunded=False)
            if status == "delivered" and rng.random() < 0.05:
                item.refunded = True
                item.refund = Refund(
                    amount_cents=paid,
                    include_shipping=False,
                    reason="changed_mind",
                    idempotency_key=f"seed-order-{number}-{product.name}",
                )
            items.append(item)

        order = Order(
            order_number=number,
            customer=rng.choice(customers),
            status=status,
            placed_at=placed_at,
            delivered_at=delivered_at,
            shipping_cents=rng.choice(SHIPPING_CHOICES),
            items=items,
        )
        session.add(order)


def _approval(
    approval_id: str,
    order: Order,
    item: OrderItem,
    *,
    status: str,
    amount_cents: int,
    max_allowed_cents: int,
    flags: list[str],
    explanation: str,
    reason: str | None,
    created_at: datetime,
) -> Approval:
    args = {
        "order_number": order.order_number,
        "item_id": item.id,
        "amount_cents": amount_cents,
        "include_shipping": False,
        "reason": "changed_mind",
    }
    thread_id = f"seed-thread-{approval_id}"
    return Approval(
        id=approval_id,
        thread_id=thread_id,
        tool_call_id=f"seed-call-{approval_id}",
        tool="issue_refund",
        args_json=args,
        payload={
            "approval_id": approval_id,
            "thread_id": thread_id,
            "tool": "issue_refund",
            "args": {**args, "amount_cents": max_allowed_cents},
            "max_allowed_cents": max_allowed_cents,
            "flags": flags,
            "agent_explanation": explanation,
            "policy_sources": ["refund_policy.md", "returns_policy.md"],
        },
        status=status,
        reviewer_id=REVIEWER_EMAIL,
        reason=reason,
        created_at=created_at,
        decided_at=created_at + timedelta(minutes=12),
    )


async def seed_review_history(session: AsyncSession, now: datetime | None = None) -> None:
    """Three already-decided approvals (approved, edited, rejected) and two tickets.

    Pending approvals are not seeded on purpose: a pending request needs a paused agent
    run, which only exists when a customer chats. Ask for a refund in the chat to get one.
    """
    now = now or _utc_now()
    orders = await session.scalars(
        select(Order)
        .where(Order.order_number >= str(FIRST_RANDOM_ORDER_NUMBER))
        .order_by(Order.order_number)
        .options(selectinload(Order.items))
    )
    items = [(order, item) for order in orders for item in order.items]
    refunded = [(o, i) for o, i in items if i.refunded]
    high_value = [
        (o, i)
        for o, i in items
        if o.status == "delivered" and not i.refunded and i.price_paid_cents >= 20_000
    ]
    history: list[Approval] = []

    if refunded:
        order, item = refunded[0]
        refund = await session.scalar(select(Refund).where(Refund.order_item_id == item.id))
        approval = _approval(
            "seed-approved-1",
            order,
            item,
            status="approved",
            amount_cents=refund.amount_cents,
            max_allowed_cents=refund.amount_cents,
            flags=["exception"],
            explanation="Outside the 30-day window but inside the 37-day grace period.",
            reason="Within the grace period, approved.",
            created_at=now - timedelta(days=4),
        )
        refund.approval_id = approval.id
        history.append(approval)

    if len(high_value) >= 2:
        order, item = high_value[0]
        edited_amount = round(item.price_paid_cents * 0.8)
        approval = _approval(
            "seed-edited-1",
            order,
            item,
            status="edited",
            amount_cents=edited_amount,
            max_allowed_cents=item.price_paid_cents,
            flags=["high_value"],
            explanation="High-value refund; the item was used, so a partial refund is suggested.",
            reason="Visible wear, refunded 80%.",
            created_at=now - timedelta(days=3),
        )
        item.refunded = True
        session.add(
            Refund(
                order_item_id=item.id,
                amount_cents=edited_amount,
                include_shipping=False,
                reason="changed_mind",
                approval_id=approval.id,
                idempotency_key=f"seed-approval-{approval.id}",
            )
        )
        history.append(approval)

        order, item = high_value[1]
        history.append(
            _approval(
                "seed-rejected-1",
                order,
                item,
                status="rejected",
                amount_cents=item.price_paid_cents,
                max_allowed_cents=item.price_paid_cents,
                flags=["high_value"],
                explanation="High-value refund requested without a stated problem.",
                reason="Customer could not describe the issue; asked to contact support again.",
                created_at=now - timedelta(days=2),
            )
        )

    session.add_all(history)
    session.add_all(
        [
            Ticket(
                thread_id="seed-thread-ticket-1",
                summary="Customer says the parcel is marked delivered but never arrived.",
                priority="high",
                status="open",
            ),
            Ticket(
                thread_id="seed-thread-ticket-2",
                summary="Question about a warranty claim on hiking boots; answered by a human.",
                priority="normal",
                status="closed",
            ),
        ]
    )


async def truncate_all(session: AsyncSession) -> None:
    await session.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
    session.expunge_all()


async def main(reset: bool, if_empty: bool = False, users_only: bool = False) -> None:
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    async with factory() as session:
        if users_only:
            added = await seed_users(session)
            await session.commit()
            await engine.dispose()
            print(f"Added {added} demo accounts.")
            return
        if reset:
            await truncate_all(session)
        elif await session.scalar(select(func.count()).select_from(Customer)):
            if if_empty:
                added = await seed_users(session)
                await session.commit()
                await engine.dispose()
                print(f"Database already has data; nothing to seed. Added {added} demo accounts.")
                return
            sys.exit("Database already has data. Run with --reset to wipe and reseed.")
        await seed(session)
        await seed_users(session)
        await seed_review_history(session)
        await session.commit()
        orders = await session.scalar(select(func.count()).select_from(Order))
    await engine.dispose()
    print(
        f"Seeded {len(CATALOG)} products, {CUSTOMER_COUNT} customers, {orders} orders "
        f"and {len(DEMO_USERS)} demo accounts."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="wipe all tables before seeding")
    parser.add_argument(
        "--if-empty", action="store_true", help="do nothing (and succeed) if there is data already"
    )
    parser.add_argument(
        "--users-only", action="store_true", help="only add the demo accounts that are missing"
    )
    arguments = parser.parse_args()
    asyncio.run(main(arguments.reset, arguments.if_empty, arguments.users_only))
