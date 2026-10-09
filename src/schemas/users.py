import re
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime

class UserCreate(BaseModel):
    username : str = Field(min_length=2, max_length=20)
    email : EmailStr
    password : str = Field(min_length=6, max_length=20)
    roles_id : list[int] = Field(default_factory=list)
    is_active : bool = True
    is_superuser: bool = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_]+", value):
            raise ValueError("your username is not allowed")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[a-zA-Z]", value) or not re.search(r"[0-9]", value):
            raise ValueError("password must contain both letters and numbers")
        return value

class User_info_change(BaseModel):
    username : str|None = Field(min_length=2, max_length=20)
    email : EmailStr | None = None
    is_superuser: bool|None = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_]+", value):
            raise ValueError("your username is not allowed")
        return value



class UserSignUp(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    email: EmailStr
    password: str = Field(min_length=6, max_length=20)

    class Config:
        from_attributes = True




class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True