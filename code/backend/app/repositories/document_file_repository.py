from typing import Any
from uuid import UUID

from beanie import SortDirection

from app.models.document_file import DocStatus, DocumentFile
from app.repositories.base import BaseRepository
from app.utils.bson import uuid_to_bin


class DocumentFileRepository(BaseRepository[DocumentFile]):
    model = DocumentFile

    async def find_by_id(self, id: UUID) -> DocumentFile | None:
        return await DocumentFile.get(id)

    async def find_by_path(self, project_id: UUID, path: str) -> DocumentFile | None:
        return await DocumentFile.find_one({"projectId": project_id, "path": path})

    async def find_by_project(self, project_id: UUID) -> list[DocumentFile]:
        return await DocumentFile.find({"projectId": project_id}).to_list()

    async def find_by_project_sorted(
        self, project_id: UUID, status: DocStatus | None = None
    ) -> list[DocumentFile]:
        """Project documents sorted by path asc.

        Mirrors the list endpoint contract: when `status` is None, deleted
        documents are excluded; otherwise the status is matched exactly.
        """
        if status is not None:
            query: dict[str, Any] = {"projectId": project_id, "status": status.value}
        else:
            query = {"projectId": project_id, "status": {"$ne": DocStatus.deleted.value}}
        return await DocumentFile.find(query).sort([("path", SortDirection.ASCENDING)]).to_list()

    async def find_ids_by_status(self, project_id: UUID, status: DocStatus) -> list[UUID]:
        docs = await DocumentFile.find({"projectId": project_id, "status": status.value}).to_list()
        return [d.id for d in docs]

    async def find_by_paths(self, project_id: UUID, paths: list[str]) -> dict[str, DocumentFile]:
        docs = await DocumentFile.find({"projectId": project_id, "path": {"$in": paths}}).to_list()
        return {doc.path: doc for doc in docs}

    async def find_by_ids_batch(self, ids: list[UUID]) -> dict[UUID, DocumentFile]:
        id_bins = [uuid_to_bin(i) for i in ids]
        items = await DocumentFile.find({"_id": {"$in": id_bins}}).to_list()
        return {item.id: item for item in items}

    async def search_in_projects(
        self, project_ids: list[UUID], fields: list[str], pattern: Any, limit: int = 10
    ) -> list[DocumentFile]:
        """Documents of the given projects whose title or content matches `pattern`."""
        id_bins = [uuid_to_bin(i) for i in project_ids]
        return (
            await DocumentFile.find(
                {
                    "projectId": {"$in": id_bins},
                    "$or": [{field: pattern} for field in fields],
                }
            )
            .limit(limit)
            .to_list()
        )

    async def save(self, doc: DocumentFile) -> DocumentFile:
        await doc.save()
        return doc

    async def delete_by_project(self, project_id: UUID) -> int:
        result = await DocumentFile.find({"projectId": project_id}).delete()
        return result.deleted_count if result else 0
