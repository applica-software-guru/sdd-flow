from typing import Optional
from uuid import UUID

from app.utils.bson import uuid_to_bin, bin_to_uuid

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.base import utcnow




class NotificationRepository:
    async def find_by_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        query: dict = {"userId": user_id}
        if unread_only:
            query["readAt"] = None
        skip = (page - 1) * page_size
        total = await Notification.find(query).count()
        items = (
            await Notification.find(query)
            .sort([("createdAt", -1)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def count_unread(self, user_id: UUID) -> int:
        return await Notification.find({"userId": user_id, "readAt": None}).count()

    async def mark_read(
        self, notification_id: UUID, user_id: UUID
    ) -> Optional[Notification]:
        notif = await Notification.get(notification_id)
        if notif and notif.user_id == user_id and notif.read_at is None:
            notif.read_at = utcnow()
            await notif.save()
        return notif

    async def mark_all_read(self, user_id: UUID) -> int:
        col = Notification.get_pymongo_collection()
        result = await col.update_many(
            {"userId": uuid_to_bin(user_id), "readAt": None},
            {"$set": {"readAt": utcnow()}},
        )
        return result.modified_count

    async def create(self, n: Notification) -> Notification:
        await n.insert()
        return n

    async def get_preference(
        self, user_id: UUID, event_type: str
    ) -> Optional[NotificationPreference]:
        return await NotificationPreference.find_one(
            {"userId": user_id, "eventType": event_type}
        )

    async def upsert_preference(
        self, user_id: UUID, event_type: str, email_enabled: bool
    ) -> NotificationPreference:
        import uuid as _uuid
        col = NotificationPreference.get_pymongo_collection()
        now = utcnow()
        uid_bin = uuid_to_bin(user_id)
        new_id = uuid_to_bin(_uuid.uuid4())
        await col.find_one_and_update(
            {"userId": uid_bin, "eventType": event_type},
            {
                "$set": {"emailEnabled": email_enabled, "updatedAt": now},
                "$setOnInsert": {
                    "_id": new_id,
                    "userId": uid_bin,
                    "createdAt": now,
                },
            },
            upsert=True,
            return_document=True,
        )
        return await NotificationPreference.find_one(
            {"userId": user_id, "eventType": event_type}
        )

    async def delete_by_user(self, user_id: UUID) -> int:
        n_result = await Notification.find({"userId": user_id}).delete()
        p_result = await NotificationPreference.find({"userId": user_id}).delete()
        n_count = n_result.deleted_count if n_result else 0
        p_count = p_result.deleted_count if p_result else 0
        return n_count + p_count
