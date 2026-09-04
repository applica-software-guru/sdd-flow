from typing import Any
from uuid import UUID

from beanie import SortDirection

from app.models.change_request import ChangeRequest, CRStatus
from app.repositories.base import BaseRepository
from app.utils.bson import uuid_to_bin
from app.utils.mongo import raw_collection


class ChangeRequestRepository(BaseRepository[ChangeRequest]):
    model = ChangeRequest

    async def find_by_id(self, id: UUID) -> ChangeRequest | None:
        return await ChangeRequest.get(id)

    async def find_by_slug(self, project_id: UUID, slug: str) -> ChangeRequest | None:
        return await ChangeRequest.find_one({"projectId": project_id, "slug": slug})

    async def find_by_number(self, project_id: UUID, number: int) -> ChangeRequest | None:
        return await ChangeRequest.find_one({"projectId": project_id, "number": number})

    async def find_by_project(
        self,
        project_id: UUID,
        status: CRStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChangeRequest], int]:
        query: dict[str, Any] = {"projectId": project_id}
        if status is not None:
            query["status"] = status.value
        skip = (page - 1) * page_size
        total = await ChangeRequest.find(query).count()
        items = await ChangeRequest.find(query).skip(skip).limit(page_size).to_list()
        return items, total

    async def find_by_project_filtered(
        self,
        project_id: UUID,
        status: CRStatus | None = None,
        author_id: UUID | None = None,
        assignee_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChangeRequest], int]:
        """Paginated project listing sorted by number desc.

        Mirrors the web list endpoint contract: when `status` is None, deleted
        CRs are excluded; otherwise the status is matched exactly.
        """
        query: dict[str, Any] = {"projectId": project_id}
        if status is not None:
            query["status"] = status.value
        else:
            query["status"] = {"$ne": CRStatus.deleted.value}
        if author_id is not None:
            query["authorId"] = author_id
        if assignee_id is not None:
            query["assigneeId"] = assignee_id

        skip = (page - 1) * page_size
        total = await ChangeRequest.find(query).count()
        items = (
            await ChangeRequest.find(query)
            .sort([("number", SortDirection.DESCENDING)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def find_by_statuses(
        self, project_id: UUID, statuses: list[CRStatus]
    ) -> list[ChangeRequest]:
        return (
            await ChangeRequest.find(
                {"projectId": project_id, "status": {"$in": [s.value for s in statuses]}}
            )
            .sort([("createdAt", SortDirection.DESCENDING)])
            .to_list()
        )

    async def find_ids_by_status(self, project_id: UUID, status: CRStatus) -> list[UUID]:
        docs = await ChangeRequest.find({"projectId": project_id, "status": status.value}).to_list()
        return [cr.id for cr in docs]

    async def find_by_ids_in_project(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, ChangeRequest]:
        id_bins = [uuid_to_bin(i) for i in ids]
        items = await ChangeRequest.find(
            {"_id": {"$in": id_bins}, "projectId": project_id}
        ).to_list()
        return {item.id: item for item in items}

    async def find_by_paths_batch(
        self, project_id: UUID, paths: list[str]
    ) -> dict[str, ChangeRequest]:
        items = await ChangeRequest.find(
            {"projectId": project_id, "path": {"$in": paths}}
        ).to_list()
        return {item.path: item for item in items if item.path is not None}

    async def find_one_by_path_active(self, project_id: UUID, path: str) -> ChangeRequest | None:
        """First non-deleted CR stored under `path` in the project, if any."""
        return await ChangeRequest.find_one(
            {
                "projectId": project_id,
                "path": path,
                "status": {"$ne": CRStatus.deleted.value},
            }
        )

    async def search_in_projects(
        self, project_ids: list[UUID], fields: list[str], pattern: Any, limit: int = 10
    ) -> list[ChangeRequest]:
        id_bins = [uuid_to_bin(i) for i in project_ids]
        return (
            await ChangeRequest.find(
                {
                    "projectId": {"$in": id_bins},
                    "$or": [{field: pattern} for field in fields],
                }
            )
            .limit(limit)
            .to_list()
        )

    async def find_by_ids_batch(self, ids: list[UUID]) -> dict[UUID, ChangeRequest]:
        id_bins = [uuid_to_bin(i) for i in ids]
        items = await ChangeRequest.find({"_id": {"$in": id_bins}}).to_list()
        return {item.id: item for item in items}

    async def get_max_number(self, project_id: UUID) -> int:
        col = raw_collection(ChangeRequest)
        result = await col.find_one(
            {"projectId": uuid_to_bin(project_id)},
            sort=[("number", -1)],
            projection={"number": 1},
        )
        return result["number"] if result else 0

    async def save(self, doc) -> ChangeRequest:
        await doc.save()
        return doc

    async def delete_by_project(self, project_id: UUID) -> int:
        result = await ChangeRequest.find({"projectId": project_id}).delete()
        return result.deleted_count if result else 0
