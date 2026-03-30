from typing import Optional
from uuid import UUID

from app.utils.bson import uuid_to_bin, bin_to_uuid

from app.models.bug import Bug, BugStatus
from app.repositories.base import BaseRepository




class BugRepository(BaseRepository[Bug]):
    model = Bug

    async def find_by_id(self, id: UUID) -> Optional[Bug]:
        return await Bug.get(id)

    async def find_by_slug(self, project_id: UUID, slug: str) -> Optional[Bug]:
        return await Bug.find_one({"projectId": project_id, "slug": slug})

    async def find_by_number(self, project_id: UUID, number: int) -> Optional[Bug]:
        return await Bug.find_one({"projectId": project_id, "number": number})

    async def find_by_project(
        self,
        project_id: UUID,
        status: Optional[BugStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Bug], int]:
        query: dict = {"projectId": project_id}
        if status is not None:
            query["status"] = status.value
        skip = (page - 1) * page_size
        total = await Bug.find(query).count()
        items = await Bug.find(query).skip(skip).limit(page_size).to_list()
        return items, total

    async def find_by_ids_batch(self, ids: list[UUID]) -> dict[UUID, Bug]:
        id_bins = [uuid_to_bin(i) for i in ids]
        items = await Bug.find({"_id": {"$in": id_bins}}).to_list()
        return {item.id: item for item in items}

    async def get_max_number(self, project_id: UUID) -> int:
        col = Bug.get_pymongo_collection()
        result = await col.find_one(
            {"projectId": uuid_to_bin(project_id)},
            sort=[("number", -1)],
            projection={"number": 1},
        )
        return result["number"] if result else 0

    async def save(self, doc) -> Bug:
        await doc.save()
        return doc

    async def delete_by_project(self, project_id: UUID) -> int:
        result = await Bug.find({"projectId": project_id}).delete()
        return result.deleted_count if result else 0
