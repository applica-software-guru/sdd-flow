from typing import Any
from uuid import UUID

from app.models.bug import Bug, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.document_file import DocumentFile
from app.models.project import Project
from app.repositories.base import BaseRepository
from app.utils.bson import bin_to_uuid, uuid_to_bin
from app.utils.mongo import raw_collection


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def find_by_id(self, id: UUID) -> Project | None:
        return await Project.get(id)

    async def find_by_slug(self, tenant_id: UUID, slug: str) -> Project | None:
        return await Project.find_one({"tenantId": tenant_id, "slug": slug})

    async def find_by_tenant(
        self, tenant_id: UUID, include_archived: bool = False
    ) -> list[Project]:
        query: dict[str, Any] = {"tenantId": tenant_id}
        if not include_archived:
            query["archivedAt"] = None
        return await Project.find(query).to_list()

    async def find_by_ids(self, ids: list[UUID]) -> list[Project]:
        id_bins = [uuid_to_bin(i) for i in ids]
        return await Project.find({"_id": {"$in": id_bins}}).to_list()

    async def find_by_tenant_ids(
        self, tenant_ids: list[UUID], include_archived: bool = False
    ) -> list[Project]:
        if not tenant_ids:
            return []
        tenant_id_bins = [uuid_to_bin(tenant_id) for tenant_id in tenant_ids]
        query: dict[str, Any] = {"tenantId": {"$in": tenant_id_bins}}
        if not include_archived:
            query["archivedAt"] = None
        return await Project.find(query).to_list()

    async def search_in_tenant(
        self, tenant_id: UUID, pattern: Any, limit: int = 10
    ) -> list[Project]:
        """Projects of a tenant whose name or description matches `pattern`."""
        return (
            await Project.find(
                {
                    "tenantId": tenant_id,
                    "$or": [{"name": pattern}, {"description": pattern}],
                }
            )
            .limit(limit)
            .to_list()
        )

    async def get_stats_batch(self, project_ids: list[UUID]) -> dict[UUID, dict[str, int]]:
        id_bins = [uuid_to_bin(pid) for pid in project_ids]
        result: dict[UUID, dict[str, int]] = {
            pid: {"doc_count": 0, "open_cr_count": 0, "open_bug_count": 0} for pid in project_ids
        }

        doc_pipeline: list[dict[str, Any]] = [
            {"$match": {"projectId": {"$in": id_bins}}},
            {"$group": {"_id": "$projectId", "count": {"$sum": 1}}},
        ]
        cr_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "projectId": {"$in": id_bins},
                    "status": {"$nin": [CRStatus.deleted.value, CRStatus.closed.value]},
                }
            },
            {"$group": {"_id": "$projectId", "count": {"$sum": 1}}},
        ]
        bug_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "projectId": {"$in": id_bins},
                    "status": {"$nin": [BugStatus.deleted.value, BugStatus.closed.value]},
                }
            },
            {"$group": {"_id": "$projectId", "count": {"$sum": 1}}},
        ]

        doc_col = raw_collection(DocumentFile)
        cr_col = raw_collection(ChangeRequest)
        bug_col = raw_collection(Bug)

        async for row in await doc_col.aggregate(doc_pipeline):
            pid = bin_to_uuid(row["_id"])
            if pid and pid in result:
                result[pid]["doc_count"] = row["count"]

        async for row in await cr_col.aggregate(cr_pipeline):
            pid = bin_to_uuid(row["_id"])
            if pid and pid in result:
                result[pid]["open_cr_count"] = row["count"]

        async for row in await bug_col.aggregate(bug_pipeline):
            pid = bin_to_uuid(row["_id"])
            if pid and pid in result:
                result[pid]["open_bug_count"] = row["count"]

        return result

    async def save(self, doc: Project) -> Project:
        await doc.save()
        return doc

    async def delete(self, doc: Project) -> None:
        await doc.delete()
