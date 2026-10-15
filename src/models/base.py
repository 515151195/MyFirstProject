from tortoise import fields, models

from datetime import datetime
from enum import Enum

class OrgStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"

class MembershipStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"

class OrgMemberRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class OrgMemRoleInv(str, Enum):
    MEMBER = "member"
    VIEWER = "viewer"

class InvitationStatus(str, Enum):
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"

class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"
    SUBMIT = "submit"

class BaseModel(models.Model):
    id = fields.BigIntField(pk=True, index=True)

    async def to_dict(self,
                      *,
                      include_m2m: bool = False,
                      exclude: set[str]|None = None,
                      ) ->dict:
        excluded = exclude or set()
        data = {
            field : getattr(self, field)
            for field in self._meta.db_fields
            if field not in excluded
        }

        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.strftime("%Y-%m-%d %H:%M:%S")

        if include_m2m:
            for field in self._meta.m2m_fields:
                if field in excluded:
                    continue
                related_items = await getattr(self, field).all()
                data[field] = [
                    await item.to_dict(exclude=excluded) for item in related_items
                ]


        return data

    class Meta:
        abstract = True

class TimestampMixin:
    created_at = fields.DateTimeField(auto_now_add = True, index=True)
    updated_at = fields.DateTimeField(auto_now=True, index=True)