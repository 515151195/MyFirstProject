from schemas.approval import ApprovalCreate, ApprovalRequestOut, ApprovalRecordOut
from models import ApprovalRequest
from models.base import ApprovalStatus, ApprovalAction
from repositories import approval_repository
from core.status_machine import is_valid_transition

from fastapi import HTTPException
from tortoise.transactions import in_transaction

class ApprovalService:
    async def create_draft(self,
                           title: str,
                           applicant_id: int,
                           approver_id: int|None = None,
                           content: str|None = None,
    ) -> ApprovalRequestOut:
        req = await ApprovalRequest.create(
            applicant_id=applicant_id,
            approver_id=approver_id,
            title=title,
            content=content,
            status=ApprovalStatus.DRAFT,
        )
        return ApprovalRequestOut.model_validate(req)

    async def submit(
            self,
            approval_id: int,
            user_id: int,
    ) -> ApprovalRecordOut:
        async with in_transaction():
            approval = await approval_repository.get_by_id(approval_id)
            if not approval:
                raise HTTPException(404, "Approval request not found")
            if approval.applicant_id != user_id:
                raise HTTPException(403, "Only applicant can submit")
            if not is_valid_transition(approval.status, ApprovalStatus.PENDING):
                raise HTTPException(400, f"Cannot submit from status {approval.status}")
            approval.status = ApprovalStatus.PENDING
            await approval.save()
            rec = await approval_repository.create_record(approval, user_id, ApprovalAction.SUBMIT, comment="Submit approval")
            return ApprovalRecordOut.model_validate(rec)

    async def approve(self, approval_id: int, operator_id: int, comment: str | None) -> ApprovalRecordOut:
        async with in_transaction():
            req = await approval_repository.get_by_id(approval_id)
            if not req:
                raise HTTPException(404, "Approval request not found")
            if req.approver_id != operator_id:
                raise HTTPException(403, "You are not the designated approver")
            if req.applicant_id == operator_id:
                raise HTTPException(400, "Cannot approve your own request")
            target_status = ApprovalStatus.APPROVED
            if not is_valid_transition(req.status, target_status):
                raise HTTPException(400, f"Cannot approve, current state: {req.status}")
            req.status = target_status
            await req.save()
            rec = await approval_repository.create_record(req, operator_id, action=ApprovalAction.APPROVE, comment=comment)
            return ApprovalRecordOut.model_validate(rec)

    async def reject(self, approval_id: int, operator_id: int, comment: str) -> ApprovalRecordOut:
        async with in_transaction():
            req = await approval_repository.get_by_id(approval_id)
            if not req:
                raise HTTPException(404, "Approval request not found")
            if req.approver_id != operator_id:
                raise HTTPException(403, "You are not the designated approver")
            if req.applicant_id == operator_id:
                raise HTTPException(400, "Cannot reject your own request")
            target_status = ApprovalStatus.REJECTED
            if not is_valid_transition(req.status, target_status):
                raise HTTPException(400, f"Cannot reject, current state: {req.status}")
            req.status = target_status
            await req.save()
            rec = await approval_repository.create_record(req, operator_id, action=ApprovalAction.REJECT, comment=comment)
            return ApprovalRecordOut.model_validate(rec)

    async def cancel(self, approval_id: int, operator_id: int, comment: str|None) -> ApprovalRecordOut:
        async with in_transaction():
            req = await approval_repository.get_by_id(approval_id)
            if not req:
                raise HTTPException(404, "Approval request not found")
            if req.applicant_id != operator_id:
                raise HTTPException(403, "You cannot cancel others' request")
            target_status = ApprovalStatus.CANCELLED
            if not is_valid_transition(req.status, target_status):
                raise HTTPException(400, f"cannot cancel, current status: {req.status}")
            req.status = target_status
            await req.save()
            rec = await approval_repository.create_record(req, operator_id, action=ApprovalAction.CANCEL, comment=comment)
            return ApprovalRecordOut.model_validate(rec)

    async def get_one_info(self, approval_id: int, operator_id: int):
        req = await approval_repository.get_by_id(approval_id)
        if not req:
            raise HTTPException(404, "Approval request not found")
        if operator_id != req.applicant_id and operator_id != req.approver_id:
            raise HTTPException(403, "Insufficient permission")
        return ApprovalRequestOut.model_validate(req)



approval_service = ApprovalService()