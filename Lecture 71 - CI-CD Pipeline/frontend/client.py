import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any

import httpx

import config

NOT_AUTHENTICATED = "not_authenticated"
INVALID_REFRESH_TOKEN = "invalid_refresh_token"


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class StreamEvent:
    event: str
    data: dict[str, Any]


def _error_from(response: httpx.Response) -> ApiError:
    try:
        body = response.json()
        return ApiError(response.status_code, str(body["code"]), str(body["message"]))
    except ValueError, KeyError, TypeError:
        pass
    if response.status_code == 401:
        return ApiError(401, NOT_AUTHENTICATED, "Please sign in again")
    if response.status_code == 422:
        return ApiError(422, "validation_error", "The request was not accepted. Check the input.")
    return ApiError(
        response.status_code, "request_failed", f"Request failed ({response.status_code})"
    )


def _unreachable() -> ApiError:
    return ApiError(0, "unreachable", f"Cannot reach the support service at {config.API_URL}.")


def parse_sse(lines: Iterable[str]) -> Iterator[StreamEvent]:
    event, data = "message", []
    for line in lines:
        if line == "":
            if data:
                yield StreamEvent(event, _decode("\n".join(data)))
            event, data = "message", []
        elif line.startswith(":"):
            continue
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].removeprefix(" "))
    if data:
        yield StreamEvent(event, _decode("\n".join(data)))


def _decode(payload: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _request(method: str, path: str, *, token: str | None = None, **kwargs: Any) -> httpx.Response:
    headers = _bearer(token) if token else {}
    try:
        response = httpx.request(
            method,
            f"{config.API_URL}{path}",
            headers=headers,
            timeout=config.REQUEST_TIMEOUT,
            **kwargs,
        )
    except httpx.HTTPError:
        raise _unreachable() from None
    if response.is_error:
        raise _error_from(response)
    return response


def health() -> bool:
    try:
        return httpx.get(f"{config.API_URL}/health", timeout=3).is_success
    except httpx.HTTPError:
        return False


def login(email: str, password: str) -> dict[str, Any]:
    return _request("POST", "/auth/login", data={"username": email, "password": password}).json()


def register(name: str, email: str, password: str) -> dict[str, Any]:
    body = {"name": name, "email": email, "password": password}
    return _request("POST", "/auth/register", json=body).json()


def refresh(refresh_token: str) -> dict[str, Any]:
    return _request("POST", "/auth/refresh", json={"refresh_token": refresh_token}).json()


def logout(refresh_token: str) -> None:
    _request("POST", "/auth/logout", json={"refresh_token": refresh_token})


def stream_chat(message: str, thread_id: str | None, token: str) -> Iterator[StreamEvent]:
    body: dict[str, Any] = {"message": message}
    if thread_id:
        body["thread_id"] = thread_id
    timeout = httpx.Timeout(config.REQUEST_TIMEOUT, read=config.STREAM_TIMEOUT)
    try:
        with httpx.stream(
            "POST", f"{config.API_URL}/chat", json=body, headers=_bearer(token), timeout=timeout
        ) as resp:
            if resp.is_error:
                resp.read()
                raise _error_from(resp)
            yield from parse_sse(resp.iter_lines())
    except httpx.HTTPError:
        raise _unreachable() from None


def get_thread(thread_id: str, token: str) -> dict[str, Any]:
    return _request("GET", f"/threads/{thread_id}", token=token).json()


def list_threads(token: str) -> list[dict[str, Any]]:
    return _request("GET", "/threads", token=token).json()


def list_approvals(token: str, status: str, limit: int = 50) -> list[dict[str, Any]]:
    return _request(
        "GET", "/approvals", token=token, params={"status": status, "limit": limit}
    ).json()


def get_approval(token: str, approval_id: str) -> dict[str, Any]:
    return _request("GET", f"/approvals/{approval_id}", token=token).json()


def decide(
    token: str,
    approval_id: str,
    *,
    decision: str,
    edited_args: dict[str, Any] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"decision": decision}
    if edited_args is not None:
        body["edited_args"] = edited_args
    if reason:
        body["reason"] = reason
    return _request("POST", f"/approvals/{approval_id}/decision", token=token, json=body).json()


def list_documents(token: str) -> list[dict[str, Any]]:
    return _request("GET", "/documents", token=token).json()


def upload_document(token: str, name: str, content: bytes) -> dict[str, Any]:
    files = {"file": (name, content, "text/markdown")}
    return _request("POST", "/documents", token=token, files=files).json()


def delete_document(token: str, source: str) -> None:
    _request("DELETE", f"/documents/{source}", token=token)
