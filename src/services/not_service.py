from models import User, Notification, OutboxMessage
from models.base import OutboxStatus
from schemas.notification import NotificationOut

from fastapi import HTTPException
from tortoise.transactions import in_transaction


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

    async def handle_approval_success(
            self,
            outbox_id: int,
            payload: dict,
    ) -> NotificationOut:
        async with in_transaction():
            outbox_record = await OutboxMessage.get_or_none(id=outbox_id)
            if not outbox_record:
                raise HTTPException(404, "Outbox not found")
            if outbox_record.status != OutboxStatus.PENDING:
                raise HTTPException(400, "Outbox has been handled already")
            noti_record = await Notification.create(
                user_id=payload["applicant_id"],
                title="Approval success",
                content="Your approval has been passed",
                source_event_id=outbox_id,
            )
            outbox_record.status = OutboxStatus.DELIVERED
            await outbox_record.save()
            return NotificationOut.model_validate(noti_record)

    async def handle_approval_reject(
            self,
            outbox_id: int,
            payload: dict,
    ) -> NotificationOut:
        async with in_transaction():
            outbox_record = await OutboxMessage.get_or_none(id=outbox_id)
            if not outbox_record:
                raise HTTPException(404, "Outbox not found")
            if outbox_record.status != OutboxStatus.PENDING:
                raise HTTPException(400, "Outbox has been handled already")
            noti_record = await Notification.create(
                user_id=payload["applicant_id"],
                title="Approval failed",
                content="Your approval has been rejected",
                source_event_id=outbox_id,
            )
            outbox_record.status = OutboxStatus.DELIVERED
            await outbox_record.save()
            return NotificationOut.model_validate(noti_record)

    async def handle_approval_submit(
            self,
            outbox_id: int,
            payload: dict,
    ) -> NotificationOut:
        async with in_transaction():
            outbox_record = await OutboxMessage.get_or_none(id=outbox_id)
            if not outbox_record:
                raise HTTPException(404, "Outbox not found")
            if outbox_record.status != OutboxStatus.PENDING:
                raise HTTPException(400, "Outbox has been handled already")
            noti_record = await Notification.create(
                user_id=payload["approver_id"],
                title="New approval submit",
                content="There is a new approval need to handle",
                source_event_id=outbox_id,
            )
            outbox_record.status = OutboxStatus.DELIVERED
            await outbox_record.save()
            return NotificationOut.model_validate(noti_record)



notification_service = NotificationService()