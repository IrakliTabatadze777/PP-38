from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import delete, select, update

from app.config.settings import Settings
from app.db.models import RefreshToken, User
from app.security import DUMMY_HASH, create_access_token, hash_refresh_token
from scripts.seed import CUSTOMER_EMAIL, DEMO_PASSWORD
from tests.conftest import bearer_for
from tests.helpers import ADMIN_EMAIL, JWT_SECRET, REVIEWER_EMAIL

NOT_AUTHENTICATED = {"code": "not_authenticated", "message": "Please sign in again"}


async def login(client, email: str, password: str = DEMO_PASSWORD):
    return await client.post("/auth/login", data={"username": email, "password": password})


async def test_login_returns_a_token_and_the_user(serve):
    client, _ = serve()

    response = await login(client, CUSTOMER_EMAIL)

    body = response.json()
    assert response.status_code == 200
    assert body["token_type"] == "bearer" and body["expires_in"] == 900
    assert body["user"] == {"email": CUSTOMER_EMAIL, "name": "Maria Lopez", "role": "customer"}
    claims = jwt.decode(body["access_token"], JWT_SECRET, algorithms=["HS256"])
    assert claims["role"] == "customer" and claims["exp"] - claims["iat"] == 900


async def test_the_email_is_matched_without_regard_to_case_and_spaces(serve):
    client, _ = serve()

    assert (await login(client, f"  {CUSTOMER_EMAIL.upper()} ")).status_code == 200


async def test_the_issued_token_works(serve):
    client, _ = serve()
    token = (await login(client, CUSTOMER_EMAIL)).json()["access_token"]

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.json() == {"email": CUSTOMER_EMAIL, "name": "Maria Lopez", "role": "customer"}


async def test_every_login_failure_gets_the_same_answer(serve, session_factory):
    client, _ = serve()
    async with session_factory() as session:
        await session.execute(update(User).where(User.email == ADMIN_EMAIL).values(is_active=False))
        await session.commit()

    answers = [
        await login(client, CUSTOMER_EMAIL, "wrong password"),
        await login(client, "nobody@example.com"),
        await login(client, ADMIN_EMAIL),
    ]

    for response in answers:
        assert response.status_code == 401
        assert response.json() == {
            "code": "invalid_credentials",
            "message": "Wrong email or password",
        }


async def test_an_unknown_email_still_costs_one_password_check(serve, monkeypatch):
    client, _ = serve()
    checked: list[str] = []

    def spy(password: str, password_hash: str) -> bool:
        checked.append(password_hash)
        return False

    monkeypatch.setattr("app.services.auth.verify_password", spy)

    await login(client, "nobody@example.com")

    assert checked == [DUMMY_HASH]


async def test_login_needs_both_fields(serve):
    client, _ = serve()

    assert (await client.post("/auth/login", data={"username": CUSTOMER_EMAIL})).status_code == 422


async def register(client, **overrides):
    body = {"email": "sam@example.com", "name": "Sam Doe", "password": "long-enough", **overrides}
    return await client.post("/auth/register", json=body)


async def test_a_new_customer_is_registered_and_signed_in(serve, session_factory):
    client, _ = serve()

    response = await register(client, email="  Sam@Example.COM ", name=" Sam Doe ")

    body = response.json()
    assert response.status_code == 201
    assert body["user"] == {"email": "sam@example.com", "name": "Sam Doe", "role": "customer"}
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert (await client.get("/auth/me", headers=headers)).json() == body["user"]
    assert (await client.get("/threads", headers=headers)).json() == []
    async with session_factory() as session:
        stored = await session.scalar(select(User).where(User.email == "sam@example.com"))
    assert stored.password_hash.startswith("$2b$") and "long-enough" not in stored.password_hash
    assert (await login(client, "sam@example.com", "long-enough")).status_code == 200


async def test_registering_an_existing_email_is_refused_in_any_case(serve):
    client, _ = serve()

    for email in (CUSTOMER_EMAIL, CUSTOMER_EMAIL.upper()):
        response = await register(client, email=email)
        assert response.status_code == 409
        assert response.json()["code"] == "email_taken"
    assert (await login(client, CUSTOMER_EMAIL)).status_code == 200


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short"},
        {"password": "x" * 129},
        {"email": "not-an-email"},
        {"email": "a b@example.com"},
        {"name": "   "},
        {"name": ""},
    ],
)
async def test_invalid_registrations_are_refused(serve, overrides):
    client, _ = serve()

    assert (await register(client, **overrides)).status_code == 422


@pytest.mark.parametrize("role", ["admin", "reviewer"])
async def test_a_role_in_the_registration_is_ignored(serve, role):
    client, _ = serve()

    response = await register(client, role=role)

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "customer"
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert (await client.get("/documents", headers=headers)).status_code == 403


ENDPOINTS = [
    ("POST", "/chat", {"json": {"message": "hi"}}, "customer"),
    ("GET", "/threads", {}, "customer"),
    ("GET", "/threads/t-unknown", {}, "customer"),
    ("GET", "/approvals", {}, "reviewer"),
    ("GET", "/approvals/appr_unknown", {}, "reviewer"),
    ("POST", "/approvals/appr_unknown/decision", {"json": {"decision": "approve"}}, "reviewer"),
    ("GET", "/documents", {}, "admin"),
    ("DELETE", "/documents/unknown.md", {}, "admin"),
    ("POST", "/documents", {"files": {"file": ("a.md", "x", "text/markdown")}}, "admin"),
]
IDS = [f"{method} {path}" for method, path, _, _ in ENDPOINTS]


@pytest.mark.parametrize(("method", "path", "kwargs", "role"), ENDPOINTS, ids=IDS)
async def test_each_endpoint_admits_only_its_role(
    serve, customer_auth, reviewer_auth, admin_auth, method, path, kwargs, role
):
    client, _ = serve()
    by_role = {"customer": customer_auth, "reviewer": reviewer_auth, "admin": admin_auth}

    anonymous = await client.request(method, path, headers={"Authorization": ""}, **kwargs)
    assert anonymous.status_code == 401 and anonymous.json() == NOT_AUTHENTICATED
    assert anonymous.headers["www-authenticate"] == "Bearer"

    for name, headers in by_role.items():
        response = await client.request(method, path, headers=headers, **kwargs)
        if name == role:
            assert response.status_code not in (401, 403), (name, response.text)
        else:
            assert response.status_code == 403, (name, response.text)
            assert response.json() == {
                "code": "forbidden",
                "message": "You do not have access to this",
            }


async def test_health_and_login_need_no_token(serve):
    client, _ = serve()
    anonymous = {"Authorization": ""}

    assert (await client.get("/health", headers=anonymous)).status_code == 200
    assert (await login(client, CUSTOMER_EMAIL)).status_code == 200


async def test_every_signed_in_role_can_ask_who_it_is(
    serve, customer_auth, reviewer_auth, admin_auth
):
    client, _ = serve()

    roles = [
        (await client.get("/auth/me", headers=h)).json()["role"]
        for h in (customer_auth, reviewer_auth, admin_auth)
    ]

    assert roles == ["customer", "reviewer", "admin"]


async def token_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "make_token",
    [
        pytest.param(
            lambda uid: create_access_token(uid, "customer", JWT_SECRET, timedelta(minutes=-1)),
            id="expired",
        ),
        pytest.param(
            lambda uid: (
                create_access_token(uid, "customer", JWT_SECRET, timedelta(hours=1))[:-3] + "abc"
            ),
            id="tampered signature",
        ),
        pytest.param(
            lambda uid: create_access_token(
                uid, "customer", "another-secret-of-at-least-32-chars!", timedelta(hours=1)
            ),
            id="other secret",
        ),
        pytest.param(
            lambda uid: jwt.encode({"sub": str(uid), "exp": 9999999999, "iat": 1}, None, "none"),
            id="unsigned",
        ),
        pytest.param(lambda uid: "not.a.token", id="garbage"),
    ],
)
async def test_bad_tokens_are_rejected(serve, session_factory, make_token):
    client, _ = serve()
    async with session_factory() as session:
        user_id = await session.scalar(select(User.id).where(User.email == CUSTOMER_EMAIL))

    response = await client.get("/threads", headers=await token_headers(make_token(user_id)))

    assert response.status_code == 401 and response.json() == NOT_AUTHENTICATED


async def test_a_header_that_is_not_a_bearer_token_is_rejected(serve):
    client, _ = serve()

    response = await client.get("/threads", headers={"Authorization": "Basic bWFyaWE6cHc="})

    assert response.status_code == 401 and response.json() == NOT_AUTHENTICATED


async def test_a_token_stops_working_when_the_account_is_deactivated_or_deleted(
    serve, session_factory, customer_auth, reviewer_auth
):
    client, _ = serve()
    assert (await client.get("/threads", headers=customer_auth)).status_code == 200

    async with session_factory() as session:
        await session.execute(
            update(User).where(User.email == CUSTOMER_EMAIL).values(is_active=False)
        )
        await session.execute(delete(User).where(User.email == REVIEWER_EMAIL))
        await session.commit()

    for headers in (customer_auth, reviewer_auth):
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401 and response.json() == NOT_AUTHENTICATED


async def test_the_role_comes_from_the_database_not_from_the_token(serve, session_factory):
    client, _ = serve()
    headers = await bearer_for(session_factory, CUSTOMER_EMAIL)
    assert (await client.get("/approvals", headers=headers)).status_code == 403

    async with session_factory() as session:
        await session.execute(
            update(User).where(User.email == CUSTOMER_EMAIL).values(role="reviewer")
        )
        await session.commit()

    assert (await client.get("/approvals", headers=headers)).status_code == 200
    assert (await client.get("/threads", headers=headers)).status_code == 403


@pytest.mark.parametrize("secret", ["", "too-short"])
async def test_without_a_usable_secret_nothing_works(serve, monkeypatch, customer_auth, secret):
    client, _ = serve()
    monkeypatch.setattr("app.services.auth.settings", Settings(jwt_secret=secret))

    for response in (
        await login(client, CUSTOMER_EMAIL),
        await register(client),
        await client.get("/threads", headers=customer_auth),
    ):
        assert response.status_code == 503
        assert response.json()["code"] == "auth_unavailable"
    assert (await client.get("/health")).status_code == 200


async def refresh(client, token: str):
    return await client.post("/auth/refresh", json={"refresh_token": token})


async def test_login_returns_a_refresh_token_that_is_stored_only_as_a_hash(serve, session_factory):
    client, _ = serve()

    body = (await login(client, CUSTOMER_EMAIL)).json()

    assert body["refresh_expires_in"] == 7 * 24 * 3600
    async with session_factory() as session:
        rows = (await session.scalars(select(RefreshToken))).all()
    assert [row.token_hash for row in rows] == [hash_refresh_token(body["refresh_token"])]
    assert body["refresh_token"] not in rows[0].token_hash


async def test_refresh_swaps_the_token_for_a_new_pair(serve):
    client, _ = serve()
    first = (await login(client, CUSTOMER_EMAIL)).json()

    response = await refresh(client, first["refresh_token"])

    second = response.json()
    assert response.status_code == 200
    assert second["refresh_token"] != first["refresh_token"]
    assert second["user"] == first["user"] and second["expires_in"] == 900
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"})
    assert me.json()["email"] == CUSTOMER_EMAIL


async def test_a_refresh_token_works_only_once_and_reuse_ends_the_whole_chain(serve):
    client, _ = serve()
    first = (await login(client, CUSTOMER_EMAIL)).json()
    second = (await refresh(client, first["refresh_token"])).json()

    reused = await refresh(client, first["refresh_token"])
    newer = await refresh(client, second["refresh_token"])

    assert reused.status_code == 401 and reused.json()["code"] == "invalid_refresh_token"
    assert newer.status_code == 401 and newer.json()["code"] == "invalid_refresh_token"


async def test_a_new_login_is_not_affected_by_reuse_in_another_chain(serve):
    client, _ = serve()
    old = (await login(client, CUSTOMER_EMAIL)).json()
    other = (await login(client, CUSTOMER_EMAIL)).json()
    await refresh(client, old["refresh_token"])
    await refresh(client, old["refresh_token"])

    assert (await refresh(client, other["refresh_token"])).status_code == 200


async def test_unknown_and_expired_refresh_tokens_are_refused(serve, session_factory):
    client, _ = serve()
    body = (await login(client, CUSTOMER_EMAIL)).json()
    async with session_factory() as session:
        await session.execute(
            update(RefreshToken).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        await session.commit()

    for token in ("not-a-real-token", body["refresh_token"]):
        response = await refresh(client, token)
        assert response.status_code == 401 and response.json()["code"] == "invalid_refresh_token"


async def test_a_deactivated_user_cannot_refresh(serve, session_factory):
    client, _ = serve()
    body = (await login(client, CUSTOMER_EMAIL)).json()
    async with session_factory() as session:
        await session.execute(
            update(User).where(User.email == CUSTOMER_EMAIL).values(is_active=False)
        )
        await session.commit()

    response = await refresh(client, body["refresh_token"])

    assert response.status_code == 401 and response.json()["code"] == "invalid_refresh_token"


async def test_logout_revokes_the_refresh_token(serve):
    client, _ = serve()
    first = (await login(client, CUSTOMER_EMAIL)).json()
    second = (await refresh(client, first["refresh_token"])).json()

    out = await client.post("/auth/logout", json={"refresh_token": second["refresh_token"]})

    assert out.status_code == 204
    assert (await refresh(client, second["refresh_token"])).status_code == 401


async def test_logout_with_an_unknown_token_still_answers_204(serve):
    client, _ = serve()

    out = await client.post("/auth/logout", json={"refresh_token": "nothing"})

    assert out.status_code == 204


async def test_a_refresh_token_is_not_an_access_token(serve):
    client, _ = serve()
    body = (await login(client, CUSTOMER_EMAIL)).json()

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {body['refresh_token']}"})

    assert me.status_code == 401


async def test_register_also_returns_a_working_refresh_token(serve):
    client, _ = serve()
    created = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "name": "New Person", "password": "long-enough"},
    )

    response = await refresh(client, created.json()["refresh_token"])

    assert response.status_code == 200 and response.json()["user"]["email"] == "new@example.com"


async def test_refresh_is_off_without_a_usable_secret(serve, monkeypatch):
    client, _ = serve()
    monkeypatch.setattr("app.services.auth.settings", Settings(jwt_secret=""))

    response = await refresh(client, "anything")

    assert response.status_code == 503 and response.json()["code"] == "auth_unavailable"


async def test_login_clears_the_users_expired_refresh_tokens(serve, session_factory):
    client, _ = serve()
    await login(client, CUSTOMER_EMAIL)
    async with session_factory() as session:
        await session.execute(
            update(RefreshToken).values(expires_at=datetime.now(UTC) - timedelta(days=1))
        )
        await session.commit()

    await login(client, CUSTOMER_EMAIL)

    async with session_factory() as session:
        assert len((await session.scalars(select(RefreshToken))).all()) == 1
