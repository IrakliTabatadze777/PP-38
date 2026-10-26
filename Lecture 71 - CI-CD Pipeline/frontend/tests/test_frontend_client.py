import httpx
import pytest

import client
import ui


def test_parse_sse_handles_events_pings_and_split_data() -> None:
    lines = [
        ": ping",
        "event: thread",
        'data: {"thread_id": "t-1"}',
        "",
        "event: token",
        'data: {"text": "Hi"}',
        "",
        "event: done",
        "data: {}",
        "",
    ]
    events = list(client.parse_sse(lines))
    assert [e.event for e in events] == ["thread", "token", "done"]
    assert events[0].data == {"thread_id": "t-1"}
    assert events[1].data == {"text": "Hi"}


def test_parse_sse_flushes_an_event_without_a_trailing_blank_line() -> None:
    events = list(client.parse_sse(["event: done", "data: {}"]))
    assert [e.event for e in events] == ["done"]


def test_parse_sse_survives_bad_json() -> None:
    events = list(client.parse_sse(["event: token", "data: not json", ""]))
    assert events[0].data == {}


def test_error_from_uses_the_api_error_contract() -> None:
    response = httpx.Response(409, json={"code": "thread_awaiting_approval", "message": "Wait"})
    error = client._error_from(response)
    assert (error.status_code, error.code, error.message) == (
        409,
        "thread_awaiting_approval",
        "Wait",
    )


def test_error_from_never_leaks_an_unexpected_body() -> None:
    error = client._error_from(httpx.Response(500, text="Traceback (most recent call last)"))
    assert "Traceback" not in error.message


def test_unreachable_backend_becomes_an_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "request", refuse)
    with pytest.raises(client.ApiError) as caught:
        client.get_thread("t-1", "tok")
    assert caught.value.code == "unreachable"


def test_requests_carry_the_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake(method: str, url: str, **kwargs: object) -> httpx.Response:
        seen.update(method=method, url=url, headers=kwargs["headers"])
        return httpx.Response(200, json=[{"thread_id": "t-1", "title": "Hi", "updated_at": "x"}])

    monkeypatch.setattr(httpx, "request", fake)
    threads = client.list_threads("abc.def.ghi")
    assert [t["thread_id"] for t in threads] == ["t-1"]
    assert seen["method"] == "GET" and str(seen["url"]).endswith("/threads")
    assert seen["headers"] == {"Authorization": "Bearer abc.def.ghi"}


def test_login_posts_the_credentials_as_a_form(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake(method: str, url: str, **kwargs: object) -> httpx.Response:
        seen.update(method=method, url=url, data=kwargs["data"], headers=kwargs["headers"])
        return httpx.Response(200, json={"access_token": "tok", "user": {"role": "customer"}})

    monkeypatch.setattr(httpx, "request", fake)
    session = client.login("maria@example.com", "pw")
    assert session["access_token"] == "tok"
    assert str(seen["url"]).endswith("/auth/login") and seen["method"] == "POST"
    assert seen["data"] == {"username": "maria@example.com", "password": "pw"}
    assert seen["headers"] == {}


def test_a_401_without_a_body_still_means_sign_in_again() -> None:
    error = client._error_from(httpx.Response(401, text="Unauthorized"))
    assert error.code == client.NOT_AUTHENTICATED


def test_decide_sends_no_reviewer_id(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake(method: str, url: str, **kwargs: object) -> httpx.Response:
        seen.update(json=kwargs["json"])
        return httpx.Response(200, json={"agent_reply": "ok"})

    monkeypatch.setattr(httpx, "request", fake)
    client.decide("tok", "a-1", decision="reject", reason="worn")
    assert seen["json"] == {"decision": "reject", "reason": "worn"}


@pytest.mark.parametrize(
    ("cents", "text"),
    [(9850, "$98.50"), (5, "$0.05"), (123456789, "$1,234,567.89"), (None, "n/a"), (-250, "-$2.50")],
)
def test_usd(cents: int | None, text: str) -> None:
    assert ui.usd(cents) == text


def test_register_posts_json_to_the_register_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake(method: str, url: str, **kwargs: object) -> httpx.Response:
        seen.update(method=method, url=url, json=kwargs.get("json"))
        return httpx.Response(201, json={"access_token": "tok"}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", fake)
    assert client.register("Sam", "sam@example.com", "long-enough") == {"access_token": "tok"}
    assert seen["method"] == "POST" and str(seen["url"]).endswith("/auth/register")
    assert seen["json"] == {"name": "Sam", "email": "sam@example.com", "password": "long-enough"}


def test_refresh_and_logout_send_the_refresh_token_in_the_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, object, object]] = []

    def fake(method: str, url: str, **kwargs: object) -> httpx.Response:
        seen.append((url.rsplit("/", 1)[-1], kwargs.get("json"), kwargs["headers"]))
        body = {"access_token": "new"} if url.endswith("refresh") else None
        return httpx.Response(200 if body else 204, json=body, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx, "request", fake)
    assert client.refresh("old-refresh") == {"access_token": "new"}
    client.logout("old-refresh")
    body = {"refresh_token": "old-refresh"}
    assert seen == [("refresh", body, {}), ("logout", body, {})]
