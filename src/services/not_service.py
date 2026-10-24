from models import User, Notification
from schemas.notification import NotificationOut

from fastapi import HTTPException


class NotificationService:
    async def set_is_read(self, notification_id: int, user: User):
        notification = await Notification.get_or_none(id=notification_id)
        if not notification:
            raise HTTPException(404, "Notification not found")
        if not notification.user_id == user.id:
            raise HTTPException(403, "No right to do this")
        notification.is_read = True
        await notification.save()
        return NotificationOut.model_validate(notification)


notification_service = NotificationService()