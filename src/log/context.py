from contextvars import ContextVar, Token
from uuid import uuid4

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

def set_request_id(value: str|None = None) -> tuple[str, Token]:
    request_id = value or uuid4().hex[:8]
    token = request_id_var.set(request_id)
    return request_id, token

def get_request_id() -> str:
    return request_id_var.get()


def reset_request_id(token: Token) -> None:
    request_id_var.reset(token)