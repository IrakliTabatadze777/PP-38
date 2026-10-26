from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.config import policy
from app.money import format_usd

Decision = Literal["eligible", "needs_human_judgment", "ineligible", "not_applicable"]


@dataclass(frozen=True)
class EligibilityResult:
    decision: Decision
    rule_ids: tuple[str, ...]
    max_refund_cents: int
    shipping_included: bool
    explanation: str
    warranty_years: int | None = None


def evaluate_refund(
    *,
    order_status: str,
    delivered_at: datetime | None,
    now: datetime,
    price_paid_cents: int,
    refundable_shipping_cents: int,
    final_sale: bool,
    category: str,
    reason: str,
    already_refunded: bool,
) -> EligibilityResult:
    if order_status != "delivered" or delivered_at is None:
        return _not_applicable(order_status)
    if already_refunded:
        return EligibilityResult(
            "ineligible", ("BR-7",), 0, False, "This item has already been refunded."
        )

    damaged = reason in policy.DAMAGE_REASONS
    if final_sale and not damaged:
        return EligibilityResult(
            "ineligible", ("BR-4",), 0, False, "Final-sale items cannot be returned unless damaged."
        )

    days = (now - delivered_at).days
    if days <= policy.RETURN_WINDOW_DAYS:
        if damaged:
            max_cents = price_paid_cents + refundable_shipping_cents
            shipping_note = (
                "original shipping included"
                if refundable_shipping_cents
                else "shipping is not refundable here"
            )
            return EligibilityResult(
                "eligible",
                ("BR-2", "BR-6"),
                max_cents,
                refundable_shipping_cents > 0,
                f"Damaged or defective, delivered {days} days ago. Refundable up to "
                f"{format_usd(max_cents)}, {shipping_note}.",
            )
        return EligibilityResult(
            "eligible",
            ("BR-1", "BR-5", "BR-6"),
            price_paid_cents,
            False,
            f"Delivered {days} days ago, within the return window. Refundable up to "
            f"{format_usd(price_paid_cents)}; shipping is not refunded on ordinary returns.",
        )

    if days <= policy.GRACE_PERIOD_END_DAYS:
        return EligibilityResult(
            "needs_human_judgment",
            ("BR-3", "BR-6"),
            price_paid_cents,
            False,
            f"Delivered {days} days ago, just outside the return window. "
            "A reviewer must decide whether to make an exception.",
        )

    warranty_years = policy.WARRANTY_YEARS.get(category) if damaged else None
    explanation = f"Delivered {days} days ago, outside the return window."
    if warranty_years:
        explanation += (
            f" Manufacturing defects on this product are covered by a {warranty_years}-year "
            "warranty; offer to escalate the warranty claim."
        )
    return EligibilityResult(
        "ineligible",
        ("BR-1", "BR-8") if warranty_years else ("BR-1",),
        0,
        False,
        explanation,
        warranty_years,
    )


def _not_applicable(order_status: str) -> EligibilityResult:
    if order_status == "cancelled":
        explanation = "The order was cancelled, so there is nothing to refund."
    else:
        explanation = (
            f"The order has not been delivered yet (status: {order_status}). "
            "Suggest waiting for delivery or cancelling the order."
        )
    return EligibilityResult("not_applicable", (), 0, False, explanation)
