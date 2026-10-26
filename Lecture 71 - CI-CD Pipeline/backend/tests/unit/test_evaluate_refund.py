from datetime import UTC, datetime, timedelta

import pytest

from app.config import policy
from app.money import format_usd
from app.tools.eligibility import evaluate_refund

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)


def evaluate(days_ago: int | None = 3, **overrides):
    params = {
        "order_status": "delivered",
        "delivered_at": NOW - timedelta(days=days_ago) if days_ago is not None else None,
        "now": NOW,
        "price_paid_cents": 8900,
        "refundable_shipping_cents": 950,
        "final_sale": False,
        "category": "jackets",
        "reason": "changed_mind",
        "already_refunded": False,
    }
    return evaluate_refund(**{**params, **overrides})


@pytest.mark.parametrize(
    ("label", "kwargs", "decision", "max_cents", "shipping"),
    [
        ("within window", {"days_ago": 3}, "eligible", 8900, False),
        ("last day of window", {"days_ago": 30}, "eligible", 8900, False),
        ("damaged within window", {"days_ago": 3, "reason": "damaged"}, "eligible", 9850, True),
        (
            "defective within window",
            {"days_ago": 30, "reason": "defective"},
            "eligible",
            9850,
            True,
        ),
        (
            "final sale but damaged",
            {"days_ago": 5, "final_sale": True, "reason": "damaged"},
            "eligible",
            9850,
            True,
        ),
        ("grace period starts", {"days_ago": 31}, "needs_human_judgment", 8900, False),
        ("grace period ends", {"days_ago": 37}, "needs_human_judgment", 8900, False),
        (
            "damaged in grace period",
            {"days_ago": 33, "reason": "damaged"},
            "needs_human_judgment",
            8900,
            False,
        ),
        ("after grace period", {"days_ago": 38}, "ineligible", 0, False),
        (
            "defective after grace period",
            {"days_ago": 60, "reason": "defective"},
            "ineligible",
            0,
            False,
        ),
        ("final sale", {"days_ago": 5, "final_sale": True}, "ineligible", 0, False),
        (
            "final sale in grace period",
            {"days_ago": 33, "final_sale": True},
            "ineligible",
            0,
            False,
        ),
        ("already refunded", {"days_ago": 10, "already_refunded": True}, "ineligible", 0, False),
        ("shipped", {"days_ago": None, "order_status": "shipped"}, "not_applicable", 0, False),
        ("placed", {"days_ago": None, "order_status": "placed"}, "not_applicable", 0, False),
        ("cancelled", {"days_ago": None, "order_status": "cancelled"}, "not_applicable", 0, False),
    ],
)
def test_decision_table(label, kwargs, decision, max_cents, shipping):
    result = evaluate(**kwargs)
    assert result.decision == decision, label
    assert result.max_refund_cents == max_cents, label
    assert result.shipping_included is shipping, label


def test_window_boundaries_come_from_policy():
    just_inside = evaluate(days_ago=policy.RETURN_WINDOW_DAYS)
    just_outside = evaluate(days_ago=policy.RETURN_WINDOW_DAYS + 1)
    last_grace = evaluate(days_ago=policy.GRACE_PERIOD_END_DAYS)
    past_grace = evaluate(days_ago=policy.GRACE_PERIOD_END_DAYS + 1)
    assert [r.decision for r in (just_inside, just_outside, last_grace, past_grace)] == [
        "eligible",
        "needs_human_judgment",
        "needs_human_judgment",
        "ineligible",
    ]


def test_partial_days_round_down():
    delivered_at = NOW - timedelta(days=30, hours=23)
    assert evaluate(delivered_at=delivered_at).decision == "eligible"


def test_shipping_already_refunded_is_not_refunded_twice():
    result = evaluate(days_ago=3, reason="damaged", refundable_shipping_cents=0)
    assert result.max_refund_cents == 8900
    assert result.shipping_included is False


@pytest.mark.parametrize(
    ("category", "years"),
    [("boots", 1), ("jackets", 1), ("tents", 2), ("backpacks", 2), ("apparel", None)],
)
def test_late_defect_mentions_warranty(category, years):
    result = evaluate(days_ago=100, reason="defective", category=category)
    assert result.decision == "ineligible"
    assert result.warranty_years == years
    assert ("BR-8" in result.rule_ids) is (years is not None)


def test_late_change_of_mind_has_no_warranty():
    assert evaluate(days_ago=100).warranty_years is None


def test_rule_ids_are_reported():
    assert evaluate(days_ago=3, reason="damaged").rule_ids == ("BR-2", "BR-6")
    assert evaluate(days_ago=5, final_sale=True).rule_ids == ("BR-4",)
    assert evaluate(days_ago=5, already_refunded=True).rule_ids == ("BR-7",)


def test_explanation_shows_dollars():
    assert "$98.50" in evaluate(days_ago=3, reason="damaged").explanation


@pytest.mark.parametrize(
    ("cents", "text"), [(9850, "$98.50"), (5, "$0.05"), (0, "$0.00"), (123456, "$1,234.56")]
)
def test_format_usd(cents, text):
    assert format_usd(cents) == text
