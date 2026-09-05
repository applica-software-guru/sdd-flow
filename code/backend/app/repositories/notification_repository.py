from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from beanie import SortDirection
from bson.binary import Binary, UuidRepresentation

from app.models.base import utcnow
from app.models.notification import Notification
from app.models.notification_email_log import NotificationEmailLog
from app.models.notification_preference import NotificationPreference
from app.utils.bson import uuid_to_bin
from app.utils.mongo import raw_collection


class NotificationRepository:
    async def find_by_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        query: dict[str, Any] = {"userId": user_id}
        if unread_only:
            query["readAt"] = None
        skip = (page - 1) * page_size
        total = await Notification.find(query).count()
        items = (
            await Notification.find(query)
            .sort([("createdAt", SortDirection.DESCENDING)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def count_unread(self, user_id: UUID) -> int:
        return await Notification.find({"userId": user_id, "readAt": None}).count()

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        notif = await Notification.get(notification_id)
        if notif and notif.user_id == user_id and notif.read_at is None:
            notif.read_at = utcnow()
            await notif.save()
        return notif

    async def mark_all_read(self, user_id: UUID) -> int:
        col = raw_collection(Notification)
        result = await col.update_many(
            {"userId": uuid_to_bin(user_id), "readAt": None},
            {"$set": {"readAt": utcnow()}},
        )
        return result.modified_count

    async def create(self, n: Notification) -> Notification:
        await n.insert()
        return n

    async def get_preference(self, user_id: UUID, event_type: str) -> NotificationPreference | None:
        return await NotificationPreference.find_one({"userId": user_id, "eventType": event_type})

    async def upsert_preference(
        self, user_id: UUID, event_type: str, email_enabled: bool
    ) -> NotificationPreference:
        col = raw_collection(NotificationPreference)
        now = utcnow()
        uid_bin = uuid_to_bin(user_id)
        new_id = uuid_to_bin(uuid4())
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
        pref = await NotificationPreference.find_one({"userId": user_id, "eventType": event_type})
        assert pref is not None, "upsert completed but preference not found"
        return pref

    async def delete_by_entity_ids(self, tenant_id: UUID, entity_ids: list[UUID]) -> int:
        """Delete notifications linked to the given entity ids (project reset)."""
        entity_bins = [
            Binary.from_uuid(i, uuid_representation=UuidRepresentation.STANDARD) for i in entity_ids
        ]
        result = await Notification.find(
            {"tenantId": tenant_id, "entityId": {"$in": entity_bins}}
        ).delete()
        return result.deleted_count if result else 0

    async def find_preferences_by_user(self, user_id: UUID) -> list[NotificationPreference]:
        return await NotificationPreference.find({"userId": user_id}).to_list()

    async def find_recent_email_log(
        self,
        user_id: UUID,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        since: datetime,
    ) -> bool:
        """True when a coalesced email was already sent inside `since`."""
        existing = await NotificationEmailLog.find_one(
            {
                "userId": user_id,
                "eventType": event_type,
                "entityType": entity_type,
                "entityId": entity_id,
                "sentAt": {"$gte": since},
            }
        )
        return existing is not None

    async def record_email_sent(
        self,
        tenant_id: UUID,
        user_id: UUID,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
    ) -> None:
        await NotificationEmailLog(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
        ).insert()

    async def delete_by_user(self, user_id: UUID) -> int:
        n_result = await Notification.find({"userId": user_id}).delete()
        p_result = await NotificationPreference.find({"userId": user_id}).delete()
        n_count = n_result.deleted_count if n_result else 0
        p_count = p_result.deleted_count if p_result else 0
        return n_count + p_count
