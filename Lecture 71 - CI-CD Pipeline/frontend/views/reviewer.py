from typing import Any

import streamlit as st

import client
import config
import ui

STATUSES = ["pending", "approved", "edited", "rejected"]
FLAG_LABELS = {"high_value": "High value", "exception": "Outside the return window"}
TOOL_LABELS = {"issue_refund": "Refund request", "issue_replacement": "Replacement request"}
STATUS_COLORS = {"pending": "orange", "approved": "green", "edited": "blue", "rejected": "red"}


def flash(kind: str, message: str) -> None:
    st.session_state.reviewer_flash = (kind, message)


def submit(token: str, approval_id: str, **decision: Any) -> None:
    with st.spinner("Saving your decision and waiting for the assistant…"):
        try:
            done = client.decide(token, approval_id, **decision)
        except client.ApiError as error:
            ui.check_session(error)
            flash("error", error.message)
        else:
            flash("success", f"Saved. The assistant told the customer: {done['agent_reply']}")
    st.rerun()


def decision_controls(token: str, detail: dict[str, Any]) -> None:
    approval_id = detail["approval_id"]
    is_refund = detail["tool"] == "issue_refund"
    labels = ["Approve", "Change amount", "Reject"] if is_refund else ["Approve", "Reject"]
    tabs = st.tabs(labels)

    with tabs[0]:
        if st.button("Approve as proposed", key=f"approve-{approval_id}", type="primary"):
            submit(token, approval_id, decision="approve")

    if is_refund:
        with tabs[1]:
            maximum = (detail["max_allowed_cents"] or 0) / 100
            proposed = min(detail["args"].get("amount_cents", 0) / 100, maximum)
            dollars = st.number_input(
                "Refund amount (USD)",
                min_value=0.0,
                max_value=maximum,
                value=proposed,
                step=0.01,
                format="%.2f",
                key=f"amount-{approval_id}",
            )
            if st.button("Approve this amount", key=f"edit-{approval_id}"):
                submit(
                    token,
                    approval_id,
                    decision="edit",
                    edited_args={"amount_cents": round(dollars * 100)},
                )

    with tabs[-1]:
        reason = st.text_area(
            "Reason (the assistant explains this to the customer)",
            key=f"reason-{approval_id}",
            max_chars=1000,
        )
        if st.button("Reject", key=f"reject-{approval_id}"):
            if reason.strip():
                submit(token, approval_id, decision="reject", reason=reason.strip())
            else:
                st.warning("Give a reason to reject.")


def approval_card(token: str, detail: dict[str, Any]) -> None:
    args = detail["args"]
    with st.container(border=True):
        st.subheader(TOOL_LABELS.get(detail["tool"], "Request"))
        st.badge(detail["status"].capitalize(), color=STATUS_COLORS[detail["status"]])
        for flag in detail["flags"]:
            st.badge(FLAG_LABELS.get(flag, flag), color="orange", icon=":material/flag:")
        st.caption(
            f"Order {args.get('order_number', '?')}, item {args.get('item_id', '?')} · "
            f"conversation {detail['thread_id']}"
        )
        if detail["tool"] == "issue_refund":
            proposed, maximum = st.columns(2)
            shipping = " (with shipping)" if args.get("include_shipping") else ""
            proposed.metric("Proposed amount", ui.usd(args.get("amount_cents")) + shipping)
            maximum.metric("Maximum allowed", ui.usd(detail["max_allowed_cents"]))
        st.markdown(f"**Reason given:** {args.get('reason', 'n/a')}")
        st.markdown("**What the records show**")
        st.write(detail["agent_explanation"] or "n/a")
        st.caption("Policy sources: " + (", ".join(detail["policy_sources"]) or "none"))
        if detail["status"] == "pending":
            decision_controls(token, detail)
        else:
            outcome = f"Decided by {detail['reviewer_id'] or 'unknown'}"
            if detail["reason"]:
                outcome += f". Reason: {detail['reason']}"
            st.caption(outcome)


def render_queue(status: str) -> None:
    token = ui.token()
    try:
        summaries = client.list_approvals(token, status)
        details = [client.get_approval(token, s["approval_id"]) for s in summaries]
    except client.ApiError as error:
        ui.show_error(error)
        return
    if not details:
        st.info(f"Nothing {status}.")
    for detail in details:
        approval_card(token, detail)


ui.require_token()
ui.backend_status()

st.title("Approval queue")
st.caption(
    "Refunds and replacements wait here until a person decides. "
    "Nothing is sent to the customer's payment method before that."
)
if "reviewer_flash" in st.session_state:
    kind, message = st.session_state.pop("reviewer_flash")
    (st.success if kind == "success" else st.error)(message)

status = st.segmented_control("Show", STATUSES, default="pending", format_func=str.capitalize)
status = status or "pending"
refresh = config.QUEUE_POLL_SECONDS if status == "pending" else None
st.fragment(run_every=refresh)(render_queue)(status)
