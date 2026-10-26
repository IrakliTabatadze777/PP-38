from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    secret_is_usable,
    verify_password,
)

SECRET = "unit-test-secret-of-at-least-32-chars"


def test_a_password_matches_only_its_own_hash():
    stored = hash_password("correct horse")

    assert stored != "correct horse" and stored.startswith("$2b$")
    assert verify_password("correct horse", stored)
    assert not verify_password("wrong horse", stored)


def test_hashes_are_salted_and_garbage_hashes_never_match():
    assert hash_password("same") != hash_password("same")
    assert not verify_password("same", "not-a-hash")
    assert not verify_password("same", "")


def test_a_token_carries_the_user_id():
    token = create_access_token(42, "reviewer", SECRET, timedelta(minutes=5))

    assert decode_access_token(token, SECRET) == 42
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert claims["role"] == "reviewer" and claims["sub"] == "42"
    assert claims["exp"] - claims["iat"] == 300


def test_an_expired_token_is_rejected():
    long_ago = datetime.now(UTC) - timedelta(hours=2)
    token = create_access_token(1, "customer", SECRET, timedelta(hours=1), now=long_ago)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, SECRET)


def test_a_token_signed_with_another_secret_is_rejected():
    token = create_access_token(1, "customer", "another-secret-of-at-least-32-chars!", timedelta(1))

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token, SECRET)


def test_a_token_that_names_no_algorithm_is_rejected():
    claims = {"sub": "1", "iat": datetime.now(UTC), "exp": datetime.now(UTC) + timedelta(hours=1)}
    unsigned = jwt.encode(claims, None, algorithm="none")

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(unsigned, SECRET)


SOON = int(datetime.now(UTC).timestamp()) + 3600


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "1"},
        {"sub": "1", "exp": SOON},
        {"iat": 1, "exp": SOON},
        {"sub": "not-a-number", "iat": 1, "exp": SOON},
    ],
)
def test_a_token_missing_a_claim_or_with_a_bad_subject_is_rejected(claims):
    token = jwt.encode(claims, SECRET, algorithm="HS256")

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token, SECRET)


@pytest.mark.parametrize("secret,usable", [("", False), ("short", False), ("x" * 32, True)])
def test_the_secret_must_be_long_enough(secret, usable):
    assert secret_is_usable(secret) is usable


def test_refresh_tokens_are_random_and_stored_as_a_fixed_size_hash():
    first, second = new_refresh_token(), new_refresh_token()

    assert first != second and len(first) >= 48
    assert hash_refresh_token(first) == hash_refresh_token(first)
    assert hash_refresh_token(first) != hash_refresh_token(second)
    assert len(hash_refresh_token(first)) == 64 and first not in hash_refresh_token(first)
