from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Customer, Order, OrderItem, Refund


async def find_for_customer(session: AsyncSession, order_number: str, email: str) -> Order | None:
    return await session.scalar(
        select(Order)
        .join(Customer)
        .where(
            Order.order_number == order_number.strip(),
            func.lower(Customer.email) == email.strip().lower(),
        )
        .options(joinedload(Order.items).joinedload(OrderItem.product))
    )


async def get_item(session: AsyncSession, order_number: str, item_id: int) -> OrderItem | None:
    return await session.scalar(
        select(OrderItem)
        .join(Order)
        .where(Order.order_number == order_number, OrderItem.id == item_id)
        .options(joinedload(OrderItem.order), joinedload(OrderItem.product))
    )


async def shipping_already_refunded(session: AsyncSession, order_id: int) -> bool:
    refund_id = await session.scalar(
        select(Refund.id)
        .join(OrderItem)
        .where(OrderItem.order_id == order_id, Refund.include_shipping.is_(True))
        .limit(1)
    )
    return refund_id is not None
