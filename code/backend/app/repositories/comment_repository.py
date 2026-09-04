from typing import Any, cast
from uuid import UUID

from app.models.comment import Comment
from app.repositories.base import BaseRepository
from app.utils.bson import bin_to_uuid, uuid_to_bin
from app.utils.mongo import raw_collection


class CommentRepository(BaseRepository[Comment]):
    model = Comment

    async def count_by_entities(self, entity_type: str, entity_ids: list[UUID]) -> dict[UUID, int]:
        if not entity_ids:
            return {}
        id_bins = [uuid_to_bin(eid) for eid in entity_ids]
        result: dict[UUID, int] = {eid: 0 for eid in entity_ids}
        pipeline: list[dict[str, Any]] = [
            {"$match": {"entityType": entity_type, "entityId": {"$in": id_bins}}},
            {"$group": {"_id": "$entityId", "count": {"$sum": 1}}},
        ]
        col = raw_collection(Comment)
        async for row in await col.aggregate(pipeline):
            row = cast(dict[str, Any], row)
            eid = bin_to_uuid(row["_id"])
            if eid and eid in result:
                result[eid] = row["count"]
        return result

    async def find_by_entity(self, entity_type: str, entity_id: UUID) -> list[Comment]:
        return await Comment.find({"entityType": entity_type, "entityId": entity_id}).to_list()

    async def find_by_id(self, id: UUID) -> Comment | None:
        return await Comment.get(id)

    async def create(self, doc: Comment) -> Comment:
        await doc.insert()
        return doc

    async def save(self, doc: Comment) -> Comment:
        await doc.save()
        return doc

    async def delete(self, doc: Comment) -> None:
        await doc.delete()

    async def delete_by_entity(self, entity_type: str, entity_id: UUID) -> int:
        result = await Comment.find({"entityType": entity_type, "entityId": entity_id}).delete()
        return result.deleted_count if result else 0

    async def delete_by_project_entities(self, cr_ids: list[UUID], bug_ids: list[UUID]) -> int:
        all_ids = [uuid_to_bin(i) for i in cr_ids + bug_ids]
        if not all_ids:
            return 0
        result = await Comment.find({"entityId": {"$in": all_ids}}).delete()
        return result.deleted_count if result else 0
