from pydantic import BaseModel, Field, field_validator

import re

class RoleCreate(BaseModel):
    name: str = Field(max_length=20)
    desc: str = Field(max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        if not re.fullmatch(r"[0-9a-zA-Z_]+", value):
            raise ValueError("Invalid role name")
        return value

class RoleOut(BaseModel):
    name: str = Field(max_length=20)
    desc: str = Field(max_length=255)

    class Config:
        from_attributes = True