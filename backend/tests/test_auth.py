"""Auth service unit tests (no HTTP server needed)."""
import asyncio
import os
import tempfile
import pytest

# Point DB at a temp file shared across all connections in this test session
_TMP = tempfile.mktemp(suffix=".db")
os.environ["DB_PATH"] = _TMP

from app.services.auth import (
    init_db, create_user, authenticate, get_user_by_email,
    decode_token, _hash_password, _verify_password, _create_token
)


@pytest.fixture(scope="module", autouse=True)
def run_init():
    asyncio.get_event_loop().run_until_complete(init_db())


def test_password_hash_verify():
    h = _hash_password("secret123")
    assert _verify_password("secret123", h)
    assert not _verify_password("wrong", h)


def test_jwt_round_trip():
    token = _create_token({"sub": 1, "email": "a@b.com"})
    payload = decode_token(token)
    assert payload["sub"] == 1
    assert payload["email"] == "a@b.com"


def test_jwt_bad_signature():
    token = _create_token({"sub": 1}) + "X"
    assert decode_token(token) is None


@pytest.mark.asyncio
async def test_create_and_login():
    user = await create_user("test@fx.ai", "pass1234", "Tester")
    assert user is not None
    assert user["email"] == "test@fx.ai"

    # Duplicate registration fails
    dup = await create_user("test@fx.ai", "pass1234")
    assert dup is None

    # Login succeeds
    token = await authenticate("test@fx.ai", "pass1234")
    assert token is not None
    payload = decode_token(token)
    assert payload["sub"] == user["id"]

    # Wrong password fails
    bad = await authenticate("test@fx.ai", "wrongpassword")
    assert bad is None
