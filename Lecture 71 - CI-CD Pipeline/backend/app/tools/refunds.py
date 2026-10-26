from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OrderItem, Refund
from app.repositories import approvals, orders, refunds, replacements
from app.schemas.tools import IssueRefundInput, IssueReplacementInput
from app.tools.eligibility import EligibilityResult
from app.tools.orders import evaluate_item


def _refund_result(refund: Refund) -> dict[str, Any]:
    return {"refund_id": refund.id, "status": "issued", "amount_cents": refund.amount_cents}


@dataclass(frozen=True)
class RefundPlan:
    item: OrderItem
    eligibility: EligibilityResult
    limit_cents: int


async def plan_refund(
    session: AsyncSession, args: IssueRefundInput, *, verified_order: str | None
) -> RefundPlan | dict[str, Any]:
    if verified_order is None or args.order_number != verified_order:
        return {"error": "order_not_verified"}
    item = await orders.get_item(session, args.order_number, args.item_id)
    if item is None:
        return {"error": "item_not_found"}

    result = await evaluate_item(session, item, args.reason)
    if result.decision not in ("eligible", "needs_human_judgment"):
        return {"error": "not_refundable", "explanation": result.explanation}
    if args.include_shipping and not result.shipping_included:
        return {"error": "shipping_not_refundable"}
    limit = result.max_refund_cents
    if not args.include_shipping:
        limit = min(limit, item.price_paid_cents)
    return RefundPlan(item=item, eligibility=result, limit_cents=limit)


async def plan_replacement(
    session: AsyncSession, args: IssueReplacementInput, *, verified_order: str | None
) -> OrderItem | dict[str, Any]:
    if verified_order is None or args.order_number != verified_order:
        return {"error": "order_not_verified"}
    item = await orders.get_item(session, args.order_number, args.item_id)
    if item is None:
        return {"error": "item_not_found"}
    if item.order.status != "delivered":
        return {"error": "order_not_delivered"}
    if item.refunded:
        return {"error": "already_refunded"}
    return item


async def issue_refund(
    session: AsyncSession,
    args: IssueRefundInput,
    *,
    thread_id: str,
    tool_call_id: str,
    verified_order: str | None,
) -> dict[str, Any]:
    key = f"{thread_id}:{tool_call_id}"
    existing = await refunds.get_by_key(session, key)
    if existing is not None:
        return _refund_result(existing)

    approval = await approvals.find_approved(session, thread_id, tool_call_id, "issue_refund")
    if approval is None:
        return {"error": "not_approved"}
    plan = await plan_refund(session, args, verified_order=verified_order)
    if isinstance(plan, dict):
        return plan
    if args.amount_cents > plan.limit_cents:
        return {"error": "amount_exceeds_limit"}

    item = plan.item
    refund = await refunds.create(
        session,
        item=item,
        amount_cents=args.amount_cents,
        include_shipping=args.include_shipping,
        reason=args.reason,
        approval_id=approval.id,
        idempotency_key=key,
    )
    if refund is None:
        existing = await refunds.get_by_key(session, key)
        return _refund_result(existing) if existing else {"error": "already_refunded"}
    return _refund_result(refund)


async def issue_replacement(
    session: AsyncSession,
    args: IssueReplacementInput,
    *,
    thread_id: str,
    tool_call_id: str,
    verified_order: str | None,
) -> dict[str, Any]:
    approval = await approvals.find_approved(session, thread_id, tool_call_id, "issue_replacement")
    if approval is None:
        return {"error": "not_approved"}
    existing = await replacements.get_by_approval(session, approval.id)
    if existing is not None:
        return {"replacement_order_id": existing.id, "status": "created"}

    item = await plan_replacement(session, args, verified_order=verified_order)
    if isinstance(item, dict):
        return item

    replacement = await replacements.create(
        session, order_item_id=item.id, reason=args.reason, approval_id=approval.id
    )
    return {"replacement_order_id": replacement.id, "status": "created"}
