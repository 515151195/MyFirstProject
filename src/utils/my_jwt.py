from settings import settings
from schemas.auth import TokenPayload

import jwt

from datetime import datetime, UTC, timedelta

def create_token(*, user_id: int, token_type: str):
    if token_type == "access":
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    elif token_type == "refresh":
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    else:
        raise ValueError(f"Unsupported token type: {token_type}")

    payload = TokenPayload(
        user_id=user_id,
        exp=expires_at,
        token_type=token_type
    )
    return jwt.encode(
        payload.model_dump(),
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

def decode_token(token: str, expected_type: str) -> TokenPayload:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("token_type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected {expected_type} type token")
    return TokenPayload(**payload)


def create_token_pair(user_id: int) -> tuple[str, str]:
    access_token = create_token(user_id=user_id, token_type="access")
    refresh_token = create_token(user_id=user_id, token_type="refresh")
    return access_token, refresh_token