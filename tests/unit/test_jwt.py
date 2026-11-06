from datetime import UTC, datetime, timedelta

import jwt
import pytest

from settings import settings
from utils.my_jwt import create_token, create_token_pair, decode_token


pytestmark = pytest.mark.unit


def test_create_and_decode_access_token():
    token = create_token(user_id=42, token_type="access")

    payload = decode_token(token, "access")

    assert isinstance(token, str)
    assert payload.user_id == 42
    assert payload.token_type == "access"


def test_create_and_decode_refresh_token():
    token = create_token(user_id=7, token_type="refresh")

    payload = decode_token(token, "refresh")

    assert payload.user_id == 7
    assert payload.token_type == "refresh"


def test_token_pair_contains_both_token_types():
    access_token, refresh_token = create_token_pair(user_id=99)

    assert access_token != refresh_token
    assert decode_token(access_token, "access").token_type == "access"
    assert decode_token(refresh_token, "refresh").token_type == "refresh"


def test_refresh_token_cannot_be_used_as_an_access_token():
    refresh_token = create_token(user_id=5, token_type="refresh")

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(refresh_token, "access")


def test_access_token_cannot_be_used_as_a_refresh_token():
    access_token = create_token(user_id=5, token_type="access")

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(access_token, "refresh")


def test_expired_token_is_rejected():
    expired_at = datetime.now(UTC) - timedelta(seconds=1)
    token = jwt.encode(
        {
            "user_id": 1,
            "token_type": "access",
            "exp": expired_at,
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, "access")


def test_token_with_wrong_signature_is_rejected():
    token = jwt.encode(
        {
            "user_id": 1,
            "token_type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "wrong-secret-key-that-is-long-enough-for-hs256",
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(token, "access")


def test_unknown_token_type_cannot_be_created():
    with pytest.raises(ValueError, match="Unsupported token type"):
        create_token(user_id=1, token_type="unknown")
