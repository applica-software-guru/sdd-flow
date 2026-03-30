from typing import Optional
from uuid import UUID

from app.models.document_file import DocumentFile
from app.repositories.base import BaseRepository


class DocumentFileRepository(BaseRepository[DocumentFile]):
    model = DocumentFile

    async def find_by_id(self, id: UUID) -> Optional[DocumentFile]:
        return await DocumentFile.get(id)

    async def find_by_path(self, project_id: UUID, path: str) -> Optional[DocumentFile]:
        return await DocumentFile.find_one({"projectId": project_id, "path": path})

    async def find_by_project(self, project_id: UUID) -> list[DocumentFile]:
        return await DocumentFile.find({"projectId": project_id}).to_list()

    async def find_by_paths(
        self, project_id: UUID, paths: list[str]
    ) -> dict[str, DocumentFile]:
        docs = await DocumentFile.find(
            {"projectId": project_id, "path": {"$in": paths}}
        ).to_list()
        return {doc.path: doc for doc in docs}

    async def save(self, doc: DocumentFile) -> DocumentFile:
        await doc.save()
        return doc

    async def delete_by_project(self, project_id: UUID) -> int:
        result = await DocumentFile.find({"projectId": project_id}).delete()
        return result.deleted_count if result else 0
