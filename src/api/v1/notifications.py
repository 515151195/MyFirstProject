from fastapi import APIRouter, Query, Depends, HTTPException

from core.dependencies import get_current_user
from schemas.base import ResponseBase
from schemas.notification import NotificationOut
from models import User, Notification
from services import notification_service

router = APIRouter()

@router.get("/notifications", summary="Get your notifications list")
async def get_notifications_list(
        page: int = Query(1),
        page_size: int = Query(20),
        user: User = Depends(get_current_user)
) -> ResponseBase[list[NotificationOut]]:
    skip = (page-1)*page_size
    items = await Notification.filter(user_id=user.id).offset(skip).limit(page_size).all()
    if not items:
        raise HTTPException(404, "Notifications not found")
    data = [NotificationOut.model_validate(item) for item in items]
    return ResponseBase(code=200, msg="Your notifications are listed: ", data=data)

@router.patch("/{notification_id}/read", summary="Set notification's is_read True")
async def is_read(
        notification_id: int,
        user: User = Depends(get_current_user),
) -> ResponseBase[NotificationOut]:
    data = await notification_service.set_is_read(notification_id, user)
    return ResponseBase(code=201, msg="Selected notification is read", data=data)