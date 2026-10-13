import secrets
import hashlib

from models import Organization, Invitation, User, Membership
from models.base import InvitationStatus
from schemas.invitation import InvitationCreate, InvitationOut

from fastapi import HTTPException
from tortoise.transactions import in_transaction
from datetime import datetime, UTC

class InvitationRepository:
    async def send_invitation(self, inv_info: InvitationCreate, sender: User):
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        raw_dict = inv_info.model_dump()
        org = await Organization.filter(id=inv_info.org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization Not Found!")
        raw_dict["org"]=org
        del raw_dict["org_id"]
        inv = await Invitation.create(**raw_dict,
                         inviter=sender,
                         token_hash=token_hash
        )
        inv_dict = await inv.to_dict()
        data = InvitationOut(**inv_dict,
                             org_name=inv.org.name,
                             inviter_name=inv.inviter.username)
        return raw_token, data

    async def accept_invitation(self, current_user: User, inv_info: Invitation, token: str):
        token_hashed = hashlib.sha256(token.encode()).hexdigest()
        if current_user.email != inv_info.invitee_email:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        if token_hashed != inv_info.token_hash:
            raise HTTPException(status_code=401, detail="Wrong token")
        if inv_info.expire_at < datetime.now(UTC):
            raise HTTPException(status_code=400, detail="Invitation has expired")
        async with in_transaction():
            exist_membership = await Membership.filter(user=current_user, org=inv_info.org).first()
            if exist_membership:
                raise HTTPException(status_code=400, detail="You are already a member of this organization")
            new_membership = await Membership.create(
                user=current_user,
                org=inv_info.org,
                role=inv_info.role,
            )
            inv_info.status = InvitationStatus.USED
            await inv_info.save()
        return new_membership

invitation_repository = InvitationRepository()