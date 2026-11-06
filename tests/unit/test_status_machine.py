import pytest

from core.status_machine import is_valid_transition
from models.base import ApprovalStatus


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ApprovalStatus.DRAFT, ApprovalStatus.PENDING),
        (ApprovalStatus.DRAFT, ApprovalStatus.CANCELLED),
        (ApprovalStatus.PENDING, ApprovalStatus.APPROVED),
        (ApprovalStatus.PENDING, ApprovalStatus.REJECTED),
        (ApprovalStatus.PENDING, ApprovalStatus.CANCELLED),
    ],
)
def test_valid_approval_transitions(
    current: ApprovalStatus,
    target: ApprovalStatus,
):
    assert is_valid_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ApprovalStatus.DRAFT, ApprovalStatus.APPROVED),
        (ApprovalStatus.DRAFT, ApprovalStatus.REJECTED),
        (ApprovalStatus.PENDING, ApprovalStatus.DRAFT),
        (ApprovalStatus.APPROVED, ApprovalStatus.PENDING),
        (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED),
        (ApprovalStatus.REJECTED, ApprovalStatus.APPROVED),
        (ApprovalStatus.CANCELLED, ApprovalStatus.PENDING),
        (ApprovalStatus.CANCELLED, ApprovalStatus.CANCELLED),
    ],
)
def test_invalid_approval_transitions(
    current: ApprovalStatus,
    target: ApprovalStatus,
):
    assert not is_valid_transition(current, target)


@pytest.mark.parametrize(
    "final_status",
    [
        ApprovalStatus.APPROVED,
        ApprovalStatus.REJECTED,
        ApprovalStatus.CANCELLED,
    ],
)
def test_final_statuses_have_no_outgoing_transitions(final_status: ApprovalStatus):
    assert all(
        not is_valid_transition(final_status, target)
        for target in ApprovalStatus
    )
