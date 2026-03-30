from typing import Optional
from uuid import UUID

from app.utils.bson import uuid_to_bin, bin_to_uuid

from app.models.comment import Comment
from app.repositories.base import BaseRepository




class CommentRepository(BaseRepository[Comment]):
    model = Comment

    async def find_by_entity(self, entity_type: str, entity_id: UUID) -> list[Comment]:
        return await Comment.find(
            {"entityType": entity_type, "entityId": entity_id}
        ).to_list()

    async def find_by_id(self, id: UUID) -> Optional[Comment]:
        return await Comment.get(id)

    async def save(self, doc: Comment) -> Comment:
        await doc.save()
        return doc

    async def delete(self, doc: Comment) -> None:
        await doc.delete()

    async def delete_by_entity(self, entity_type: str, entity_id: UUID) -> int:
        result = await Comment.find(
            {"entityType": entity_type, "entityId": entity_id}
        ).delete()
        return result.deleted_count if result else 0

    async def delete_by_project_entities(
        self, cr_ids: list[UUID], bug_ids: list[UUID]
    ) -> int:
        all_ids = [uuid_to_bin(i) for i in cr_ids + bug_ids]
        if not all_ids:
            return 0
        result = await Comment.find({"entityId": {"$in": all_ids}}).delete()
        return result.deleted_count if result else 0
