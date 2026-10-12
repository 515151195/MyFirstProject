from schemas.invitation import InvitationCreate, InvitationOut
from repositories.invitation import invitation_repository
from schemas.membership import MembershipOut
from models import User, Membership, Invitation

from fastapi import HTTPException


class InvService:
    async def create_inv(self,
                         inv_info: InvitationCreate,
    ) -> tuple[InvitationOut, str]:
        token, data = invitation_repository.send_invitation(inv_info)
        return data, token

    async def accept_inv(self,
                         user: User,
                         token: str,
                         inv_id: int,
    ) -> MembershipOut:
        invitation = await Invitation.filter(id=inv_id).first()
        if not invitation:
            raise HTTPException(404, "Invitation not found")
        membership = await invitation_repository.accept_invitation(user, invitation, token)
        return MembershipOut.model_validate(membership)



inv_service = InvService()