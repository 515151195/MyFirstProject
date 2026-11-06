from __future__ import annotations

from typing import Any


def bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_id(user_or_id: int | Any) -> int:
    user_id = getattr(user_or_id, "id", user_or_id)
    if not isinstance(user_id, int):
        raise TypeError("Expected a user id or an object with an integer id")
    return user_id


def auth_headers(user_or_id: int | Any, token_type: str = "access") -> dict[str, str]:
    from utils.my_jwt import create_token

    return bearer_headers(
        create_token(user_id=_user_id(user_or_id), token_type=token_type)
    )


def refresh_token_for_user(user_or_id: int | Any) -> str:
    from utils.my_jwt import create_token

    return create_token(user_id=_user_id(user_or_id), token_type="refresh")
