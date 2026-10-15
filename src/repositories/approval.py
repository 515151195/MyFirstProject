from models import ApprovalRequest, ApprovalRecord
from models.base import ApprovalAction, ApprovalStatus
from schemas.approval import ApprovalRecordOut

from tortoise.expressions import Q


class ApprovalRepo:
    async def get_by_id(self, id: int):
        return await ApprovalRequest.get_or_none(id=id)

    async def create_record(self,
                            req: ApprovalRequest,
                            operator_id: int,
                            action: ApprovalAction,
                            comment: str,
    ) -> ApprovalRecordOut:
        data = await ApprovalRecord.create(
            approval_request=req,
            operator_id=operator_id,
            action=action,
            comment=comment,
        )
        return ApprovalRecordOut.model_validate(data)

    async def get_approval_list(self,
                                is_applicant: bool,
                                user_id: int,
    ):
        if is_applicant:
            q = Q(applicant_id=user_id)
        else:
            q = Q(approver_id=user_id, status=ApprovalStatus.PENDING)
        return await ApprovalRequest.filter(q).order_by("-created_at")



approval_repository = ApprovalRepo()