from datetime import datetime

from pydantic import BaseModel, Field, field_validator
import re

class OrgCreate(BaseModel):
    name: str = Field(max_length=32, min_length=2)
    desc: str = Field(max_length=255)

    @field_validator("name")
    def validate(cls, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_]+", value):
            raise ValueError("Invalid org name")
        return value

class OrgOut(BaseModel):
    id: int
    name: str = Field(max_length=32, min_length=2)
    desc: str = Field(max_length=255)
    created_at : datetime

    class Config:
        from_attributes = True
    #这一步允许 Pydantic 直接读取 ORM 对象（Tortoise 实例）的属性，自动转成 Pydantic 模型。
    #实例代码如下：
    #org = await Organization.get(id=org_id)
    #out = OrgOut.model_validate(org)
    #return out