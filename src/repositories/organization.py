from schemas.organization import OrgCreate
from models import Organization, User, Membership
from models.base import OrgStatus

from fastapi import HTTPException

class OrgRepository:
    async def create_org(self, org_info: OrgCreate, current_user: User) -> Organization:
        org = await Organization.create(
            **org_info.model_dump(exclude_unset=True),
            status=OrgStatus.ACTIVE,
            owner=current_user
        )
        return org

    async def get_org_by_username(self, username: str):
        memberships = await Membership.filter(
            user__username=username
        ).prefetch_related("org").all()

        orgs = [item.org for item in memberships]
        return orgs

    async def users_of_org(self, org_name: str):
        memberships = await Membership.filter(
            org__name=org_name
        ).prefetch_related("user").all()

        users = [item.user for item in memberships]

org_repository = OrgRepository()