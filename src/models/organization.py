from .base import (TimestampMixin, BaseModel, OrgStatus,
                   OrgMemberRole, MembershipStatus,
                   InvitationStatus)

from tortoise import fields

class Organization(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=32, min_length=2, unique=True, index=True)
    desc = fields.CharField(max_length=255)
    status = fields.CharEnumField(OrgStatus, default=OrgStatus.PENDING)
    owner = fields.ForeignKeyField("models.User", related_name="owned_orgs")

    class Meta:
        table = "Organization"


class Membership(BaseModel, TimestampMixin):
    user = fields.ForeignKeyField("models.User", related_name="memberships")
    org = fields.ForeignKeyField("models.Organization", related_name="members")
    role = fields.CharEnumField(OrgMemberRole)
    status = fields.CharEnumField(MembershipStatus, default=MembershipStatus.ACTIVE)

    class Meta:
        table = "Membership"
        unique_together = ("user", "org")

class Invitation(BaseModel, TimestampMixin):
    org = fields.ForeignKeyField(
        "models.Organization",
        related_name="invitations"
    )
    inviter = fields.ForeignKeyField(
        "models.User",
        related_name="sent_invitations"
    )
    invitee_email = fields.CharField(max_length=128)
    role = fields.CharEnumField(OrgMemberRole)
    token_hash = fields.CharField(max_length=255)
    expire_at = fields.DatetimeField()
    status = fields.CharEnumField(InvitationStatus, default=InvitationStatus.PENDING)

    class Meta:
        table = "invitations"