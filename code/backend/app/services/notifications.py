import uuid

from app.models.notification import Notification
from app.repositories import NotificationRepository


async def create_notification(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    event_type: str,
    entity_type: str,
    entity_id: uuid.UUID,
    title: str,
    notification_repo: NotificationRepository = None,
) -> Notification:
    if notification_repo is None:
        notification_repo = NotificationRepository()
    notification = Notification(
        user_id=user_id,
        tenant_id=tenant_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        title=title,
    )
    return await notification_repo.create(notification)
