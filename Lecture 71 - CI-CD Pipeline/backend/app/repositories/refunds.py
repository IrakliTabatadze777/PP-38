from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OrderItem, Refund


async def get_by_key(session: AsyncSession, idempotency_key: str) -> Refund | None:
    return await session.scalar(select(Refund).where(Refund.idempotency_key == idempotency_key))


async def create(
    session: AsyncSession,
    *,
    item: OrderItem,
    amount_cents: int,
    include_shipping: bool,
    reason: str,
    approval_id: str,
    idempotency_key: str,
) -> Refund | None:
    refund = Refund(
        order_item_id=item.id,
        amount_cents=amount_cents,
        include_shipping=include_shipping,
        reason=reason,
        approval_id=approval_id,
        idempotency_key=idempotency_key,
    )
    try:
        async with session.begin_nested():
            session.add(refund)
            item.refunded = True
    except IntegrityError:
        return None
    return refund
