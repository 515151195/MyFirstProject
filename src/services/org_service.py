from schemas.organization import OrgOut, OrgCreate
from schemas.membership import MembershipOut
from models import User, Organization, Membership, Invitation
from models.base import OrgStatus, OrgMemberRole, MembershipStatus
from schemas.users import UserOut

from fastapi import HTTPException
from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction

class OrgService:
    async def create_org(org_in: OrgCreate, user: User) -> OrgOut:
        exist_org = await Organization.filter(name=org_in.name).exists()
        if exist_org:
            raise HTTPException(status_code=400, detail="Already exists the same name")
        try:
            async with in_transaction():
                org = await Organization.create(
                    **org_in.model_dump(),
                    status=OrgStatus.ACTIVE,
                    owner=user
                )
                await Membership.create(
                    user=user,
                    org=org,
                    role=OrgMemberRole.OWNER,
                    status=MembershipStatus.ACTIVE
                )
        except IntegrityError:
            raise HTTPException(status_code=400, detail="An organization with this name already exists")
        data = OrgOut.model_validate(org)
        return data

    async def get_org_users(self, org_id: int) -> list[UserOut]:
        memberships = await Membership.filter(org__id=org_id).prefetch_related("user").all()
        users = [UserOut.model_validate(item.user) for item in memberships]
        return users

    async def get_user_orgs(self, user_id: int) -> list[OrgOut]:
        memberships = await Membership.filter(user__id=user_id).prefetch_related("org").all()
        orgs = [OrgOut.model_validate(item.org) for item in memberships]
        return orgs

    async def change_name_org(self, new_name: str, org_id: int) -> OrgOut:
        if len(new_name)>32 or len(new_name)<2:
            raise HTTPException(status_code=400, detail="Invalid name")
        exist_org = await Organization.filter(name=new_name).exists()
        if exist_org:
            raise HTTPException(status_code=400, detail="Name already exists")
        org = await Organization.filter(id=org_id).first()
        if not org:
            raise HTTPException(status_code=400, detail="Invalid organization id")
        org.name = new_name
        await org.save()
        return OrgOut.model_validate(org)

    async def set_admin(self, org_id: int, user_id: int) ->MembershipOut:
        mem = await Membership.filter(org__id=org_id, user__id=user_id).first()
        if mem:
            if mem.role == OrgMemberRole.ADMIN:
                raise HTTPException(400, "This user is admin already")
            if mem.role == OrgMemberRole.OWNER:
                raise HTTPException(403, "WTF you wanna do")
            mem.role = OrgMemberRole.ADMIN
            await mem.save()
        else:
            raise HTTPException(404, "User is not in this organization")

        return MembershipOut.model_validate(mem)

    async def delete_my_org(self, org_id: int):
        org = await Organization.filter(id=org_id).first()
        if not org:
            raise HTTPException(404, "Selected organization was not found")
        async with in_transaction():
            await Membership.filter(org=org).delete()
            await Invitation.filter(org=org).delete()
            await org.delete()

    async def remove_member(self, org_id: int, user_id: int):
        user = await User.filter(id=user_id).first()
        if not user:
            raise HTTPException(404, "Invalid user id")
        membership = await Membership.filter(org__id=org_id, user__id=user.id).first()
        if not membership:
            raise HTTPException(404, "No such a member")
        if membership.role == OrgMemberRole.OWNER or membership.role == OrgMemberRole.ADMIN:
            raise HTTPException(403, "You have no right to do this")
        async with in_transaction():
            await Membership.filter(org__id=org_id, user__id=user_id).delete()
            await Invitation.filter(org__id=org_id, invitee_email=user.email).delete()



org_service = OrgService()