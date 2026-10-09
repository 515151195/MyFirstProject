from pydantic import BaseModel, Field, field_validator
from datetime import datetime

import re

class Credentials(BaseModel):
    username : str = Field(min_length=1, max_length=20)
    password : str = Field(min_length=6, max_length=32)

class TokenPayload(BaseModel):
    user_id: int
    exp: datetime
    token_type: str = "access"

class RefreshRequest(BaseModel):
    refresh_token: str

class ChangePassword(BaseModel):
    old_password: str = Field(min_length=6, max_length=32)
    new_password: str = Field(min_length=6, max_length=32)
    new_password_again: str = Field(min_length=6, max_length=32)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[a-zA-Z]", value) or not re.search(r"[0-9]", value):
            raise ValueError("Invalid password")

        return value