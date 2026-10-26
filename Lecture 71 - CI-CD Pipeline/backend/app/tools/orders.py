from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OrderItem
from app.repositories import orders
from app.schemas.tools import CheckRefundEligibilityInput, LookupOrderInput
from app.tools.eligibility import EligibilityResult, evaluate_refund

NOT_FOUND = {"error": "not_found"}


async def lookup_order(session: AsyncSession, args: LookupOrderInput) -> dict[str, Any]:
    order = await orders.find_for_customer(session, args.order_number, args.email)
    if order is None:
        return dict(NOT_FOUND)
    items = [
        {
            "item_id": item.id,
            "name": item.product.name,
            "price_cents": item.price_paid_cents,
            "final_sale": item.product.final_sale,
            "refunded": item.refunded,
        }
        for item in order.items
    ]
    return {
        "order_number": order.order_number,
        "status": order.status,
        "placed_at": order.placed_at.isoformat(),
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "items": items,
        "shipping_cents": order.shipping_cents,
        "total_cents": sum(i["price_cents"] for i in items) + order.shipping_cents,
    }


async def evaluate_item(
    session: AsyncSession, item: OrderItem, reason: str, now: datetime | None = None
) -> EligibilityResult:
    shipping_refunded = await orders.shipping_already_refunded(session, item.order_id)
    return evaluate_refund(
        order_status=item.order.status,
        delivered_at=item.order.delivered_at,
        now=now or datetime.now(UTC),
        price_paid_cents=item.price_paid_cents,
        refundable_shipping_cents=0 if shipping_refunded else item.order.shipping_cents,
        final_sale=item.product.final_sale,
        category=item.product.category,
        reason=reason,
        already_refunded=item.refunded,
    )


async def check_refund_eligibility(
    session: AsyncSession,
    args: CheckRefundEligibilityInput,
    *,
    verified_order: str | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    if verified_order is None or args.order_number != verified_order:
        return {"error": "order_not_verified"}
    item = await orders.get_item(session, args.order_number, args.item_id)
    if item is None:
        return {"error": "item_not_found"}
    result = await evaluate_item(session, item, args.reason, now)
    return {
        "decision": result.decision,
        "rule_ids": list(result.rule_ids),
        "max_refund_cents": result.max_refund_cents,
        "explanation": result.explanation,
    }
