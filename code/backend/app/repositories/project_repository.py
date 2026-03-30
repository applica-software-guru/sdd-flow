from typing import Optional
from uuid import UUID

from app.utils.bson import uuid_to_bin, bin_to_uuid

from app.models.project import Project
from app.models.document_file import DocumentFile
from app.models.change_request import ChangeRequest, CRStatus
from app.models.bug import Bug, BugStatus
from app.repositories.base import BaseRepository




class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def find_by_id(self, id: UUID) -> Optional[Project]:
        return await Project.get(id)

    async def find_by_slug(self, tenant_id: UUID, slug: str) -> Optional[Project]:
        return await Project.find_one({"tenantId": tenant_id, "slug": slug})

    async def find_by_tenant(
        self, tenant_id: UUID, include_archived: bool = False
    ) -> list[Project]:
        query: dict = {"tenantId": tenant_id}
        if not include_archived:
            query["archivedAt"] = None
        return await Project.find(query).to_list()

    async def get_stats_batch(self, project_ids: list[UUID]) -> dict[UUID, dict]:
        id_bins = [uuid_to_bin(pid) for pid in project_ids]
        result: dict[UUID, dict] = {pid: {"doc_count": 0, "open_cr_count": 0, "open_bug_count": 0} for pid in project_ids}

        doc_pipeline = [
            {"$match": {"projectId": {"$in": id_bins}}},
            {"$group": {"_id": "$projectId", "count": {"$sum": 1}}},
        ]
        cr_pipeline = [
            {"$match": {"projectId": {"$in": id_bins}, "status": {"$nin": [CRStatus.deleted.value, CRStatus.closed.value]}}},
            {"$group": {"_id": "$projectId", "count": {"$sum": 1}}},
        ]
        bug_pipeline = [
            {"$match": {"projectId": {"$in": id_bins}, "status": {"$nin": [BugStatus.deleted.value, BugStatus.closed.value]}}},
            {"$group": {"_id": "$projectId", "count": {"$sum": 1}}},
        ]

        doc_col = DocumentFile.get_pymongo_collection()
        cr_col = ChangeRequest.get_pymongo_collection()
        bug_col = Bug.get_pymongo_collection()

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

    async def save(self, project: Project) -> Project:
        await project.save()
        return project

    async def delete(self, project: Project) -> None:
        await project.delete()
