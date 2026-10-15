from fastapi import APIRouter, Depends

from schemas.approval import ApprovalCreate, ApprovalRequestOut, ApprovalRecordOut
from core.dependencies import get_current_user
from models import User
from schemas.base import ResponseBase
from services import approval_service
from repositories import approval_repository


router = APIRouter()

@router.post("/organization/{org_id}/draft", summary="Create approval draft")
async def create_draft(org_id: int, approval_data: ApprovalCreate, user: User = Depends(get_current_user)) -> ResponseBase[ApprovalRequestOut]:
    data = await approval_service.create_draft(
        org_id=org_id,
        title=approval_data.title,
        applicant_id=user.id,
        approver_id=approval_data.approver_id,
        content=approval_data.content,
    )
    return ResponseBase(code=201, msg="Approval draft created success", data=data)

@router.post("/{approval_id}/submit", summary="Submit approval")
async def submit_approval(
        approval_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase[ApprovalRecordOut]:
    data = await approval_service.submit(approval_id, user.id)
    return ResponseBase(code=201, msg="Approval submit success", data=data)

@router.post("/{approval_id}/approve", summary="Approve request")
async def approve_request(
        approval_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase[ApprovalRecordOut]:
    data = await approval_service.approve(approval_id, user.id, "Approve request")
    return ResponseBase(code=201, msg="Request approved success", data=data)

@router.post("/{approval_id}/reject", summary="Reject approval request")
async def reject_request(
        approval_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase[ApprovalRecordOut]:
    data = await approval_service.reject(approval_id, user.id, "reject")
    return ResponseBase(code=201, msg="reject success", data=data)

@router.post("/{approval_id}/cancel", summary="Cancel my request")
async def cancel_request(
        approval_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase[ApprovalRecordOut]:
    data = await approval_service.cancel(approval_id, user.id, "cancel my request")
    return ResponseBase(code=201, msg="Request canceled success", data=data)

@router.get("/{approval_id}", summary="Get information of approval")
async def get_approval_info(
        approval_id: int,
        user: User = Depends(get_current_user)
) -> ResponseBase[ApprovalRequestOut]:
    data = await approval_service.get_one_info(approval_id, user.id)
    return ResponseBase(code=200, msg="Request information get success", data=data)

@router.get("/list", summary="List approvals of applicants or approvers")
async def get_approval_list(
        is_applicant: bool = False,
        user: User = Depends(get_current_user)
) -> ResponseBase[list[ApprovalRequestOut]]:
    requests = await approval_repository.get_approval_list(is_applicant, user.id)
    data = [ApprovalRequestOut.model_validate(item) for item in requests]
    return ResponseBase(code=200, msg="Approvals list get success", data=data)