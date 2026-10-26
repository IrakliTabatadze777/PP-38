import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Approval, Order, OrderItem, Refund, Replacement, Ticket
from app.schemas.tools import (
    CheckRefundEligibilityInput,
    EscalateToHumanInput,
    IssueRefundInput,
    IssueReplacementInput,
    LookupOrderInput,
)
from app.tools.escalation import escalate_to_human
from app.tools.orders import check_refund_eligibility, lookup_order
from app.tools.refunds import issue_refund, issue_replacement
from scripts.seed import CUSTOMER_EMAIL, seed

THREAD = "t-test"


@pytest.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    await seed(db_session)
    await db_session.commit()
    return db_session


async def item_id(session: AsyncSession, order_number: str) -> int:
    return await session.scalar(
        select(OrderItem.id).join(Order).where(Order.order_number == order_number)
    )


async def approve(
    session: AsyncSession, tool: str, tool_call_id: str, status: str = "approved"
) -> None:
    session.add(
        Approval(
            id=f"appr_{tool_call_id}",
            thread_id=THREAD,
            tool_call_id=tool_call_id,
            tool=tool,
            args_json={},
            status=status,
        )
    )
    await session.flush()


def refund_args(item: int, amount: int = 9850, shipping: bool = True, reason: str = "damaged"):
    return IssueRefundInput(
        order_number="1042",
        item_id=item,
        amount_cents=amount,
        include_shipping=shipping,
        reason=reason,
    )


async def refund_count(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Refund))


async def test_lookup_order_returns_order_details(seeded):
    result = await lookup_order(seeded, LookupOrderInput(order_number="1042", email=CUSTOMER_EMAIL))
    assert result["order_number"] == "1042"
    assert result["status"] == "delivered"
    assert result["shipping_cents"] == 950
    assert result["total_cents"] == 9850
    [item] = result["items"]
    assert item["name"] == "Alpine Shell Jacket"
    assert item["price_cents"] == 8900
    assert item["final_sale"] is False
    assert item["refunded"] is False


async def test_lookup_order_email_is_case_insensitive(seeded):
    result = await lookup_order(
        seeded, LookupOrderInput(order_number=" 1042 ", email="Customer@Example.com ")
    )
    assert result["order_number"] == "1042"


@pytest.mark.parametrize(
    ("order_number", "email"),
    [
        ("1042", "someone.else@example.com"),
        ("9999", CUSTOMER_EMAIL),
        ("9999", "nobody@example.com"),
    ],
)
async def test_lookup_order_failures_look_identical(seeded, order_number, email):
    result = await lookup_order(seeded, LookupOrderInput(order_number=order_number, email=email))
    assert result == {"error": "not_found"}


@pytest.mark.parametrize(
    ("order_number", "reason", "decision"),
    [
        ("1042", "changed_mind", "eligible"),
        ("1043", "changed_mind", "needs_human_judgment"),
        ("1044", "changed_mind", "ineligible"),
        ("1045", "changed_mind", "ineligible"),
        ("1046", "changed_mind", "ineligible"),
        ("1047", "changed_mind", "not_applicable"),
    ],
)
async def test_scenario_orders(seeded, order_number, reason, decision):
    item = await item_id(seeded, order_number)
    result = await check_refund_eligibility(
        seeded,
        CheckRefundEligibilityInput(order_number=order_number, item_id=item, reason=reason),
        verified_order=order_number,
    )
    assert result["decision"] == decision


async def test_damaged_jacket_includes_shipping(seeded):
    item = await item_id(seeded, "1042")
    result = await check_refund_eligibility(
        seeded,
        CheckRefundEligibilityInput(order_number="1042", item_id=item, reason="damaged"),
        verified_order="1042",
    )
    assert result["decision"] == "eligible"
    assert result["max_refund_cents"] == 9850


async def test_eligibility_requires_verified_order(seeded):
    item = await item_id(seeded, "1042")
    args = CheckRefundEligibilityInput(order_number="1042", item_id=item, reason="damaged")
    expected = {"error": "order_not_verified"}
    assert await check_refund_eligibility(seeded, args, verified_order=None) == expected
    assert await check_refund_eligibility(seeded, args, verified_order="1043") == expected


async def test_eligibility_rejects_item_from_another_order(seeded):
    other_item = await item_id(seeded, "1043")
    result = await check_refund_eligibility(
        seeded,
        CheckRefundEligibilityInput(order_number="1042", item_id=other_item, reason="damaged"),
        verified_order="1042",
    )
    assert result == {"error": "item_not_found"}


async def test_refund_without_human_decision_is_refused(seeded):
    item = await item_id(seeded, "1042")
    before = await refund_count(seeded)
    result = await issue_refund(
        seeded, refund_args(item), thread_id=THREAD, tool_call_id="call_1", verified_order="1042"
    )
    assert result == {"error": "not_approved"}
    assert await refund_count(seeded) == before


@pytest.mark.parametrize("status", ["pending", "rejected"])
async def test_refund_needs_an_approving_decision(seeded, status):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_refund", "call_1", status)
    result = await issue_refund(
        seeded, refund_args(item), thread_id=THREAD, tool_call_id="call_1", verified_order="1042"
    )
    assert result == {"error": "not_approved"}


async def test_decision_for_another_tool_call_does_not_count(seeded):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_refund", "call_other")
    result = await issue_refund(
        seeded, refund_args(item), thread_id=THREAD, tool_call_id="call_1", verified_order="1042"
    )
    assert result == {"error": "not_approved"}


async def test_approved_refund_creates_row_and_marks_item(seeded):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_refund", "call_1")
    result = await issue_refund(
        seeded, refund_args(item), thread_id=THREAD, tool_call_id="call_1", verified_order="1042"
    )
    assert result["status"] == "issued"
    assert result["amount_cents"] == 9850
    refund = await seeded.scalar(select(Refund).where(Refund.id == result["refund_id"]))
    assert refund.include_shipping is True
    assert refund.approval_id == "appr_call_1"
    assert (await seeded.get(OrderItem, item)).refunded is True


async def test_same_tool_call_twice_creates_one_refund(seeded):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_refund", "call_1")
    kwargs = {"thread_id": THREAD, "tool_call_id": "call_1", "verified_order": "1042"}
    first = await issue_refund(seeded, refund_args(item), **kwargs)
    count_after_first = await refund_count(seeded)
    second = await issue_refund(seeded, refund_args(item), **kwargs)
    assert second == first
    assert await refund_count(seeded) == count_after_first


async def test_second_refund_for_same_item_is_rejected(seeded):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_refund", "call_1")
    await approve(seeded, "issue_refund", "call_2")
    await issue_refund(
        seeded, refund_args(item), thread_id=THREAD, tool_call_id="call_1", verified_order="1042"
    )
    result = await issue_refund(
        seeded, refund_args(item), thread_id=THREAD, tool_call_id="call_2", verified_order="1042"
    )
    assert result["error"] == "not_refundable"


@pytest.mark.parametrize(
    ("amount", "shipping", "error"),
    [
        (9851, True, "amount_exceeds_limit"),
        (8901, False, "amount_exceeds_limit"),
        (10_000_00, True, "amount_exceeds_limit"),
    ],
)
async def test_model_supplied_amount_is_checked_against_database(seeded, amount, shipping, error):
    item = await item_id(seeded, "1042")
    before = await refund_count(seeded)
    await approve(seeded, "issue_refund", "call_1")
    result = await issue_refund(
        seeded,
        refund_args(item, amount, shipping),
        thread_id=THREAD,
        tool_call_id="call_1",
        verified_order="1042",
    )
    assert result == {"error": error}
    assert await refund_count(seeded) == before


async def test_shipping_not_refunded_on_ordinary_return(seeded):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_refund", "call_1")
    result = await issue_refund(
        seeded,
        refund_args(item, 9850, True, reason="changed_mind"),
        thread_id=THREAD,
        tool_call_id="call_1",
        verified_order="1042",
    )
    assert result == {"error": "shipping_not_refundable"}


async def test_reviewer_can_refund_less_than_the_limit(seeded):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_refund", "call_1", "edited")
    result = await issue_refund(
        seeded,
        refund_args(item, 6000, False),
        thread_id=THREAD,
        tool_call_id="call_1",
        verified_order="1042",
    )
    assert result["amount_cents"] == 6000


async def test_grace_period_refund_is_allowed_after_human_decision(seeded):
    item = await item_id(seeded, "1043")
    await approve(seeded, "issue_refund", "call_1")
    args = IssueRefundInput(
        order_number="1043",
        item_id=item,
        amount_cents=14000,
        include_shipping=False,
        reason="changed_mind",
    )
    result = await issue_refund(
        seeded, args, thread_id=THREAD, tool_call_id="call_1", verified_order="1043"
    )
    assert result["amount_cents"] == 14000


async def test_refund_for_unverified_or_other_order_is_refused(seeded):
    item = await item_id(seeded, "1042")
    before = await refund_count(seeded)
    await approve(seeded, "issue_refund", "call_1")
    kwargs = {"thread_id": THREAD, "tool_call_id": "call_1"}
    unverified = await issue_refund(seeded, refund_args(item), verified_order=None, **kwargs)
    wrong_order = await issue_refund(seeded, refund_args(item), verified_order="1043", **kwargs)
    assert unverified == wrong_order == {"error": "order_not_verified"}
    assert await refund_count(seeded) == before


async def test_refund_for_item_of_another_order_is_refused(seeded):
    other_item = await item_id(seeded, "1043")
    await approve(seeded, "issue_refund", "call_1")
    result = await issue_refund(
        seeded,
        refund_args(other_item),
        thread_id=THREAD,
        tool_call_id="call_1",
        verified_order="1042",
    )
    assert result == {"error": "item_not_found"}


async def test_refund_for_old_order_is_refused_even_if_approved(seeded):
    item = await item_id(seeded, "1044")
    await approve(seeded, "issue_refund", "call_1")
    args = IssueRefundInput(
        order_number="1044",
        item_id=item,
        amount_cents=24900,
        include_shipping=False,
        reason="changed_mind",
    )
    result = await issue_refund(
        seeded, args, thread_id=THREAD, tool_call_id="call_1", verified_order="1044"
    )
    assert result["error"] == "not_refundable"


async def test_shipping_is_refunded_once_per_order(seeded):
    order = await seeded.scalar(select(Order).where(Order.order_number == "1042"))
    first_item = await item_id(seeded, "1042")
    second = OrderItem(order_id=order.id, product_id=1, price_paid_cents=1000, refunded=False)
    seeded.add(second)
    await seeded.flush()
    await approve(seeded, "issue_refund", "call_1")
    await approve(seeded, "issue_refund", "call_2")
    kwargs = {"thread_id": THREAD, "verified_order": "1042"}
    await issue_refund(seeded, refund_args(first_item), tool_call_id="call_1", **kwargs)
    result = await issue_refund(
        seeded, refund_args(second.id, 1950), tool_call_id="call_2", **kwargs
    )
    assert result == {"error": "shipping_not_refundable"}


def replacement_args(item: int, order_number: str = "1042"):
    return IssueReplacementInput(order_number=order_number, item_id=item, reason="damaged")


async def test_replacement_needs_human_decision(seeded):
    item = await item_id(seeded, "1042")
    result = await issue_replacement(
        seeded,
        replacement_args(item),
        thread_id=THREAD,
        tool_call_id="call_1",
        verified_order="1042",
    )
    assert result == {"error": "not_approved"}


async def test_approved_replacement_is_created_once(seeded):
    item = await item_id(seeded, "1042")
    await approve(seeded, "issue_replacement", "call_1")
    kwargs = {"thread_id": THREAD, "tool_call_id": "call_1", "verified_order": "1042"}
    first = await issue_replacement(seeded, replacement_args(item), **kwargs)
    second = await issue_replacement(seeded, replacement_args(item), **kwargs)
    assert first["status"] == "created"
    assert second == first
    assert await seeded.scalar(select(func.count()).select_from(Replacement)) == 1


async def test_replacement_for_undelivered_order_is_refused(seeded):
    item = await item_id(seeded, "1047")
    await approve(seeded, "issue_replacement", "call_1")
    result = await issue_replacement(
        seeded,
        replacement_args(item, "1047"),
        thread_id=THREAD,
        tool_call_id="call_1",
        verified_order="1047",
    )
    assert result == {"error": "order_not_delivered"}


async def test_escalation_creates_ticket(seeded):
    result = await escalate_to_human(
        seeded, EscalateToHumanInput(summary="Wants a person", priority="high"), thread_id=THREAD
    )
    ticket = await seeded.get(Ticket, result["ticket_id"])
    assert ticket.thread_id == THREAD
    assert ticket.priority == "high"
    assert ticket.status == "open"
