from schemas.invitation import InvitationCreate, InvitationOut
from repositories.invitation import invitation_repository
from schemas.membership import MembershipOut
from models import User, Membership, Invitation
from models.base import InvitationStatus
from core.permissions import require_org_role

from fastapi import HTTPException
from tortoise.transactions import in_transaction


class InvService:
    async def create_inv(self,
                         inv_info: InvitationCreate,
                         sender: User,
    ) -> tuple[InvitationOut, str]:
        token, data = await invitation_repository.send_invitation(inv_info, sender)
        return data, token

    async def accept_inv(self,
                         user: User,
                         token: str,
                         inv_id: int,
    ) -> MembershipOut:
        invitation = await Invitation.filter(id=inv_id).first()
        if not invitation:
            raise HTTPException(404, "Invitation not found")
        if not invitation.status == InvitationStatus.PENDING:
            raise HTTPException(400, "Invalid invitation")
        membership = await invitation_repository.accept_invitation(user, invitation, token)
        return MembershipOut.model_validate(membership)

    async def disable_inv(self,
                          inv_id: int,
                          user: User,
    ) -> InvitationOut:
        inv = await Invitation.filter(id=inv_id).prefetch_related("org", "inviter").first()
        if not inv:
            raise HTTPException(404, "Invitation not found")
        if inv.status == InvitationStatus.REVOKED:
            raise HTTPException(400, "Disabled invitation")
        if inv.status == InvitationStatus.USED:
            raise HTTPException(400, "Invitation has been used")
        if await require_org_role(user.id, inv.org.id):
            inv.status = InvitationStatus.REVOKED
            await inv.save()
            return InvitationOut(**await inv.to_dict(),
                                 org_name=inv.org.name,
                                 inviter_name=inv.inviter.username,
            )
        raise HTTPException(403, "No permission")



inv_service = InvService()