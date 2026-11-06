from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

from models import (
    ApprovalRequest,
    Invitation,
    Membership,
    Notification,
    Organization,
    OutboxMessage,
    Role,
    User,
)
from models.base import (
    ApprovalStatus,
    InvitationStatus,
    MembershipStatus,
    OrgMemberRole,
    OrgStatus,
    OutboxStatus,
)
from utils.password import hash_password


DEFAULT_PASSWORD = "Password123"


async def create_user(
    username: str,
    email: str,
    role: Role | None = None,
    *,
    password: str = DEFAULT_PASSWORD,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    user = await User.create(
        username=username,
        email=email,
        password=hash_password(password),
        is_active=is_active,
        is_superuser=is_superuser,
    )
    if role is not None:
        await user.roles.add(role)
    return user


async def create_org(
    name: str,
    owner: User,
    *,
    desc: str = "Test organization",
    status: OrgStatus = OrgStatus.ACTIVE,
    add_owner_membership: bool = True,
) -> Organization:
    organization = await Organization.create(
        name=name,
        desc=desc,
        owner=owner,
        status=status,
    )
    if add_owner_membership:
        await Membership.create(
            user=owner,
            org=organization,
            role=OrgMemberRole.OWNER,
            status=MembershipStatus.ACTIVE,
        )
    return organization


async def add_member(
    organization: Organization,
    user: User,
    *,
    role: OrgMemberRole = OrgMemberRole.MEMBER,
    status: MembershipStatus = MembershipStatus.ACTIVE,
) -> Membership:
    return await Membership.create(
        user=user,
        org=organization,
        role=role,
        status=status,
    )


async def create_invitation(
    organization: Organization,
    inviter: User,
    invitee_email: str,
    *,
    role: OrgMemberRole = OrgMemberRole.MEMBER,
    token: str | None = None,
    expire_at: datetime | None = None,
    status: InvitationStatus = InvitationStatus.PENDING,
) -> tuple[Invitation, str]:
    raw_token = token or secrets.token_urlsafe(32)
    invitation = await Invitation.create(
        org=organization,
        inviter=inviter,
        invitee_email=invitee_email,
        role=role,
        token_hash=sha256(raw_token.encode()).hexdigest(),
        expire_at=expire_at or datetime.now(UTC) + timedelta(days=1),
        status=status,
    )
    return invitation, raw_token


async def create_approval(
    organization: Organization,
    applicant: User,
    approver: User,
    *,
    title: str = "Expense approval",
    content: str | None = "Test approval content",
    status: ApprovalStatus = ApprovalStatus.DRAFT,
) -> ApprovalRequest:
    return await ApprovalRequest.create(
        organization=organization,
        applicant=applicant,
        approver=approver,
        title=title,
        content=content,
        status=status,
    )


async def create_outbox(
    event_type: str,
    payload: dict[str, Any],
    *,
    status: OutboxStatus = OutboxStatus.PENDING,
    retry_count: int = 0,
    max_retry: int = 3,
) -> OutboxMessage:
    return await OutboxMessage.create(
        event_type=event_type,
        payload=json.dumps(payload),
        status=status,
        retry_count=retry_count,
        max_retry=max_retry,
    )


async def create_notification(
    user: User,
    *,
    title: str = "Test notification",
    content: str = "Test notification content",
    is_read: bool = False,
    source_event_id: int | None = None,
) -> Notification:
    return await Notification.create(
        user_id=user.id,
        title=title,
        content=content,
        is_read=is_read,
        source_event_id=source_event_id or secrets.randbelow(2_000_000_000) + 1,
    )
