from typing import Generic, Any, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ResponseBase(BaseModel, Generic[T]):
    code: int = 200
    msg: str
    data: T | None = None
    extra_data: int | None = None