import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

import client

FRONTEND = Path(__file__).resolve().parents[1]
VIEWS = FRONTEND / "views"
USERS = {
    "customer": {"email": "maria@example.com", "name": "Maria Lopez", "role": "customer"},
    "reviewer": {"email": "rev@support.example", "name": "Riley Reviewer", "role": "reviewer"},
    "admin": {"email": "admin@support.example", "name": "Alex Admin", "role": "admin"},
}

DETAIL = {
    "approval_id": "a-1",
    "thread_id": "t-1",
    "tool": "issue_refund",
    "status": "pending",
    "flags": ["high_value"],
    "amount_cents": 9850,
    "created_at": "2026-01-01T00:00:00Z",
    "args": {
        "order_number": "1042",
        "item_id": 7,
        "amount_cents": 9850,
        "include_shipping": True,
        "reason": "Broken zipper",
    },
    "max_allowed_cents": 9850,
    "agent_explanation": "Delivered 3 days ago.",
    "policy_sources": ["refund_policy.md"],
    "reviewer_id": None,
    "reason": None,
    "decided_at": None,
}


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "health", lambda: True)


def signed_in(at: AppTest, role: str = "customer") -> AppTest:
    at.session_state["token"] = "tok"
    at.session_state["user"] = USERS[role]
    return at


def run(view: str, role: str = "customer") -> AppTest:
    return signed_in(AppTest.from_file(str(VIEWS / view), default_timeout=10), role)


def run_app(role: str | None = None) -> AppTest:
    at = AppTest.from_file(str(FRONTEND / "app.py"), default_timeout=10)
    return signed_in(at, role) if role else at


def test_chat_streams_an_answer_and_keeps_it(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_stream(
        message: str, thread_id: str | None, token: str
    ) -> Iterator[client.StreamEvent]:
        yield client.StreamEvent("thread", {"thread_id": "t-1"})
        yield client.StreamEvent("tool_call", {"name": "Looking up our policies"})
        yield client.StreamEvent("token", {"text": "You can return "})
        yield client.StreamEvent("token", {"text": "unworn boots."})
        yield client.StreamEvent("done", {})

    monkeypatch.setattr(client, "stream_chat", fake_stream)
    at = run("chat.py").run()
    at.chat_input[0].set_value("Can I return boots?").run()
    assert not at.exception
    texts = [m.markdown[0].value for m in at.chat_message]
    assert "Can I return boots?" in texts
    assert "You can return unworn boots." in texts
    assert at.session_state.thread_id == "t-1"
    assert at.chat_input[0].disabled is False


def test_chat_sends_the_signed_in_token_with_the_message(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake_stream(
        message: str, thread_id: str | None, token: str
    ) -> Iterator[client.StreamEvent]:
        seen.append(token)
        yield client.StreamEvent("thread", {"thread_id": "t-1"})
        yield client.StreamEvent("done", {})

    monkeypatch.setattr(client, "stream_chat", fake_stream)
    monkeypatch.setattr(client, "list_threads", lambda _: [])
    at = run("chat.py").run()
    at.chat_input[0].set_value("hello").run()
    assert not at.exception
    assert seen == ["tok"]


def test_chat_locks_the_input_while_a_request_is_under_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_stream(
        message: str, thread_id: str | None, token: str
    ) -> Iterator[client.StreamEvent]:
        yield client.StreamEvent("thread", {"thread_id": "t-1"})
        yield client.StreamEvent("token", {"text": "I've sent this to our team."})
        yield client.StreamEvent("awaiting_approval", {"approval_id": "a-1"})

    monkeypatch.setattr(client, "stream_chat", fake_stream)
    monkeypatch.setattr(client, "get_thread", lambda _, token: {"status": "awaiting_approval"})
    at = run("chat.py").run()
    at.chat_input[0].set_value("Refund order 1042").run()
    assert not at.exception
    assert at.session_state.awaiting is True
    assert at.chat_input[0].disabled is True
    assert any("under review" in i.value or "with our team" in i.value for i in at.info)


def test_chat_shows_api_errors_without_crashing(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(message: str, thread_id: str | None, token: str) -> Iterator[client.StreamEvent]:
        raise client.ApiError(0, "unreachable", "Cannot reach the support service.")
        yield

    monkeypatch.setattr(client, "stream_chat", broken)
    at = run("chat.py").run()
    at.chat_input[0].set_value("hello").run()
    assert not at.exception
    assert [e.value for e in at.error] == ["Cannot reach the support service."]


def reviewer_app(monkeypatch: pytest.MonkeyPatch, calls: list[dict[str, Any]]) -> AppTest:
    monkeypatch.setattr(client, "list_approvals", lambda token, status, limit=50: [DETAIL])
    monkeypatch.setattr(client, "get_approval", lambda token, approval_id: DETAIL)

    def fake_decide(token: str, approval_id: str, **decision: Any) -> dict[str, Any]:
        calls.append({"approval_id": approval_id, **decision})
        return {"agent_reply": "Your refund is on its way."}

    monkeypatch.setattr(client, "decide", fake_decide)
    return run("reviewer.py", "reviewer").run()


def test_pages_ask_for_a_sign_in_when_there_is_no_token() -> None:
    for view in ("chat.py", "reviewer.py", "documents.py"):
        at = AppTest.from_file(str(VIEWS / view), default_timeout=10).run()
        assert not at.exception
        assert any("sign in" in i.value for i in at.info)


def test_reviewer_card_shows_dollars_not_cents(monkeypatch: pytest.MonkeyPatch) -> None:
    at = reviewer_app(monkeypatch, [])
    assert not at.exception
    assert [m.value for m in at.metric] == ["$98.50 (with shipping)", "$98.50"]


def test_reviewer_approve(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    at = reviewer_app(monkeypatch, calls)
    at.button(key="approve-a-1").click().run()
    assert calls == [{"approval_id": "a-1", "decision": "approve"}]
    assert any("Your refund is on its way." in s.value for s in at.success)


def test_reviewer_edit_sends_cents(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    at = reviewer_app(monkeypatch, calls)
    at.number_input(key="amount-a-1").set_value(60.5).run()
    at.button(key="edit-a-1").click().run()
    assert calls[0]["decision"] == "edit"
    assert calls[0]["edited_args"] == {"amount_cents": 6050}


def test_reviewer_reject_requires_a_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    at = reviewer_app(monkeypatch, calls)
    at.button(key="reject-a-1").click().run()
    assert calls == []
    at.text_area(key="reason-a-1").set_value("Photos show wear").run()
    at.button(key="reject-a-1").click().run()
    assert calls[0]["decision"] == "reject"
    assert calls[0]["reason"] == "Photos show wear"


def test_reviewer_shows_backend_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(token: str, status: str, limit: int = 50) -> list[dict[str, Any]]:
        raise client.ApiError(403, "forbidden", "You do not have access to this")

    monkeypatch.setattr(client, "list_approvals", deny)
    at = run("reviewer.py", "reviewer").run()
    assert not at.exception
    assert [e.value for e in at.error] == ["You do not have access to this"]


def test_documents_lists_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client, "list_documents", lambda token: [{"source": "returns_policy.md", "chunks": 6}]
    )
    at = run("documents.py", "admin").run()
    assert not at.exception
    assert any("returns_policy.md" in m.value for m in at.markdown)


def test_chat_lists_the_signed_in_customers_conversations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asked: list[str] = []

    def fake_list(token: str) -> list[dict[str, Any]]:
        asked.append(token)
        return [{"thread_id": "t-9", "title": "Order 1042 refund", "updated_at": "2026-01-01"}]

    monkeypatch.setattr(client, "list_threads", fake_list)
    at = run("chat.py").run()
    assert not at.exception
    assert asked == ["tok"]
    assert "Order 1042 refund" in [b.label for b in at.sidebar.button]
    assert not at.sidebar.text_input


def test_chat_opens_a_past_conversation(monkeypatch: pytest.MonkeyPatch) -> None:
    thread = {
        "thread_id": "t-9",
        "status": "idle",
        "messages": [
            {"role": "customer", "content": "Order 1042 refund"},
            {"role": "assistant", "content": "Done, it is on its way."},
        ],
    }
    monkeypatch.setattr(
        client, "list_threads", lambda _: [{"thread_id": "t-9", "title": "Order 1042 refund"}]
    )
    monkeypatch.setattr(client, "get_thread", lambda _, token: thread)
    at = run("chat.py").run()
    at.sidebar.button(key="history-t-9").click().run()
    assert not at.exception
    texts = [m.markdown[0].value for m in at.chat_message]
    assert "Done, it is on its way." in texts
    assert at.session_state.thread_id == "t-9"


def test_chat_shows_no_list_when_the_backend_cannot_provide_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(_: str) -> list[dict[str, Any]]:
        raise client.ApiError(503, "unreachable", "The service is unreachable")

    monkeypatch.setattr(client, "list_threads", unavailable)
    at = run("chat.py").run()
    assert not at.exception
    assert not [b for b in at.sidebar.button if b.key and b.key.startswith("history-")]


def test_login_signs_the_user_in(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, str]] = []

    def fake_login(email: str, password: str) -> dict[str, Any]:
        seen.append((email, password))
        return {"access_token": "tok", "expires_in": 3600, "user": USERS["customer"]}

    monkeypatch.setattr(client, "login", fake_login)
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    at.text_input(key="login_email").set_value(" maria@example.com ")
    at.text_input(key="login_password").set_value("secret")
    at.button[0].click().run()
    assert not at.exception
    assert seen == [("maria@example.com", "secret")]
    assert at.session_state.token == "tok" and at.session_state.user["role"] == "customer"


def test_login_shows_the_backends_message_and_keeps_the_user_signed_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(email: str, password: str) -> dict[str, Any]:
        raise client.ApiError(401, "invalid_credentials", "Wrong email or password")

    monkeypatch.setattr(client, "login", refuse)
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    at.text_input(key="login_email").set_value("maria@example.com")
    at.text_input(key="login_password").set_value("nope")
    at.button[0].click().run()
    assert [e.value for e in at.error] == ["Wrong email or password"]
    assert "token" not in at.session_state


def test_login_needs_both_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "login", lambda *_: pytest.fail("must not call the backend"))
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    at.text_input(key="login_email").set_value("maria@example.com")
    at.button[0].click().run()
    assert any("email and password" in w.value for w in at.warning)


def _fill_registration(at: AppTest, *, password: str = "long-enough", confirm: str = "long-enough"):
    at.text_input(key="register_name").set_value(" Sam Doe ")
    at.text_input(key="register_email").set_value(" sam@example.com ")
    at.text_input(key="register_password").set_value(password)
    at.text_input(key="register_confirm").set_value(confirm)
    return at


def test_register_creates_the_account_and_signs_in(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[str, str, str]] = []

    def fake_register(name: str, email: str, password: str) -> dict[str, Any]:
        seen.append((name, email, password))
        user = {"email": email, "name": name, "role": "customer"}
        return {"access_token": "tok", "expires_in": 3600, "user": user}

    monkeypatch.setattr(client, "register", fake_register)
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    _fill_registration(at).button[1].click().run()
    assert not at.exception
    assert seen == [("Sam Doe", "sam@example.com", "long-enough")]
    assert at.session_state.token == "tok" and at.session_state.user["role"] == "customer"


def test_register_shows_the_backends_message_and_stays_signed_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(name: str, email: str, password: str) -> dict[str, Any]:
        raise client.ApiError(409, "email_taken", "An account with this email already exists")

    monkeypatch.setattr(client, "register", refuse)
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    _fill_registration(at).button[1].click().run()
    assert [e.value for e in at.error] == ["An account with this email already exists"]
    assert "token" not in at.session_state


@pytest.mark.parametrize(
    ("password", "confirm", "message"),
    [("short", "short", "at least 8"), ("long-enough", "different-1", "not the same")],
)
def test_register_checks_the_password_before_calling_the_backend(
    monkeypatch: pytest.MonkeyPatch, password: str, confirm: str, message: str
) -> None:
    monkeypatch.setattr(client, "register", lambda *_: pytest.fail("must not call the backend"))
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    _fill_registration(at, password=password, confirm=confirm).button[1].click().run()
    assert any(message in w.value for w in at.warning)
    assert "token" not in at.session_state


def test_register_needs_every_field(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "register", lambda *_: pytest.fail("must not call the backend"))
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    at.text_input(key="register_email").set_value("sam@example.com")
    at.button[1].click().run()
    assert any("Fill in" in w.value for w in at.warning)


def test_the_app_shows_the_login_page_until_signed_in() -> None:
    at = run_app().run()
    assert not at.exception
    assert at.text_input(key="login_email") and at.text_input(key="login_password")
    assert not at.sidebar.button


@pytest.mark.parametrize(
    ("role", "title"),
    [
        ("customer", "Customer Support Agent"),
        ("reviewer", "Approval queue"),
        ("admin", "Knowledge base"),
    ],
)
def test_each_role_lands_on_its_own_page(
    monkeypatch: pytest.MonkeyPatch, role: str, title: str
) -> None:
    monkeypatch.setattr(client, "list_threads", lambda _: [])
    monkeypatch.setattr(client, "list_approvals", lambda *_, **__: [])
    monkeypatch.setattr(client, "list_documents", lambda _: [])
    at = run_app(role).run()
    assert not at.exception
    assert [t.value for t in at.title] == [title]
    assert any(USERS[role]["name"] in c.value and role in c.value for c in at.sidebar.caption)


def test_sign_out_forgets_the_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "list_threads", lambda _: [])
    at = run_app("customer").run()
    at.sidebar.button(key="sign_out").click().run()
    assert not at.exception
    assert "token" not in at.session_state and "user" not in at.session_state
    assert at.text_input(key="login_email")


def test_an_expired_token_sends_the_user_back_to_the_login_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def expired(token: str, status: str, limit: int = 50) -> list[dict[str, Any]]:
        raise client.ApiError(401, client.NOT_AUTHENTICATED, "Please sign in again")

    monkeypatch.setattr(client, "list_approvals", expired)
    at = run_app("reviewer").run()
    assert not at.exception
    assert "token" not in at.session_state
    assert any("session has ended" in w.value for w in at.warning)
    assert at.text_input(key="login_email")


def _expiring(at: AppTest, *, seconds_left: float) -> AppTest:
    at.session_state["refresh_token"] = "refresh-1"
    at.session_state["token_expires_at"] = time.time() + seconds_left
    return at


def test_an_access_token_about_to_expire_is_renewed_before_the_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []
    monkeypatch.setattr(
        client,
        "refresh",
        lambda refresh_token: {
            "access_token": "tok-2",
            "refresh_token": "refresh-2",
            "expires_in": 900,
            "user": USERS["customer"],
        },
    )

    def fake_list(token: str) -> list[dict[str, Any]]:
        seen.append(token)
        return []

    monkeypatch.setattr(client, "list_threads", fake_list)
    at = _expiring(run("chat.py"), seconds_left=5).run()
    assert not at.exception
    assert seen and set(seen) == {"tok-2"}
    assert at.session_state.refresh_token == "refresh-2"
    assert at.session_state.token_expires_at > time.time() + 800


def test_a_token_with_plenty_of_time_left_is_not_renewed(monkeypatch: pytest.MonkeyPatch) -> None:
    def never(refresh_token: str) -> dict[str, Any]:
        raise AssertionError("refreshed too early")

    monkeypatch.setattr(client, "refresh", never)
    monkeypatch.setattr(client, "list_threads", lambda _: [])
    at = _expiring(run("chat.py"), seconds_left=600).run()
    assert not at.exception and at.session_state.token == "tok"


def test_a_refused_refresh_token_sends_the_user_back_to_the_login_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refused(refresh_token: str) -> dict[str, Any]:
        raise client.ApiError(401, client.INVALID_REFRESH_TOKEN, "Please sign in again")

    monkeypatch.setattr(client, "refresh", refused)
    monkeypatch.setattr(client, "logout", lambda refresh_token: None)
    monkeypatch.setattr(client, "list_threads", lambda _: [])
    at = _expiring(run_app("customer"), seconds_left=-10).run()
    assert not at.exception
    assert "token" not in at.session_state
    assert any("session has ended" in w.value for w in at.warning)


def test_an_unreachable_server_during_renewal_keeps_the_user_signed_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def down(refresh_token: str) -> dict[str, Any]:
        raise client.ApiError(0, "unreachable", "Cannot reach the support service")

    monkeypatch.setattr(client, "refresh", down)
    monkeypatch.setattr(client, "list_threads", lambda _: [])
    at = _expiring(run("chat.py"), seconds_left=-10).run()
    assert at.session_state.token == "tok"


def test_sign_out_revokes_the_refresh_token(monkeypatch: pytest.MonkeyPatch) -> None:
    revoked: list[str] = []
    monkeypatch.setattr(client, "logout", revoked.append)
    monkeypatch.setattr(client, "list_threads", lambda _: [])
    at = _expiring(run_app("customer"), seconds_left=600).run()
    at.sidebar.button(key="sign_out").click().run()
    assert revoked == ["refresh-1"]
    assert "token" not in at.session_state


def test_login_keeps_the_refresh_token_in_the_session(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_login(email: str, password: str) -> dict[str, Any]:
        return {
            "access_token": "tok",
            "refresh_token": "refresh-1",
            "expires_in": 900,
            "user": USERS["customer"],
        }

    monkeypatch.setattr(client, "login", fake_login)
    at = AppTest.from_file(str(VIEWS / "login.py"), default_timeout=10).run()
    at.text_input(key="login_email").input("maria@example.com")
    at.text_input(key="login_password").input("pw")
    at.button[0].click().run()
    assert at.session_state.refresh_token == "refresh-1"
    assert at.session_state.token_expires_at > time.time() + 800
