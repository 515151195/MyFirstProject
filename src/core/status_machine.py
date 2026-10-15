from models.base import ApprovalStatus

STATE_TRANSITION = {
    ApprovalStatus.DRAFT: {ApprovalStatus.PENDING, ApprovalStatus.CANCELLED},
    ApprovalStatus.PENDING: {ApprovalStatus.REJECTED, ApprovalStatus.APPROVED, ApprovalStatus.CANCELLED},
    ApprovalStatus.APPROVED: set(),
    ApprovalStatus.REJECTED: set(),
    ApprovalStatus.CANCELLED: set()
}

def is_valid_transition(current: ApprovalStatus, target: ApprovalStatus) -> bool:
    if target in STATE_TRANSITION.get(current, set()):
        return True
    return False