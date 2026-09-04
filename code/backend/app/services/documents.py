"""Document (project docs) domain service."""

import uuid
from typing import Any

from fastapi import HTTPException, status

from app.models.document_file import DocStatus, DocumentFile
from app.repositories import DocumentFileRepository
from app.schemas.docs import DocBulkRequest, DocBulkResponse, DocCreate, DocResponse, DocUpdate
from app.services.audit import AuditService
from app.services.projects import ProjectService


class DocumentService:
    def __init__(
        self,
        project_service: ProjectService,
        doc_repo: DocumentFileRepository,
        audit_service: AuditService,
    ) -> None:
        self._project_service = project_service
        self._doc_repo = doc_repo
        self._audit_service = audit_service

    async def _get_doc_in_project_or_404(
        self, project_id: uuid.UUID, doc_id: uuid.UUID
    ) -> DocumentFile:
        doc = await self._doc_repo.find_by_id(doc_id)
        if doc is None or doc.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return doc

    async def list_docs(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        status_filter: DocStatus | None = None,
    ) -> list[DocumentFile]:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        return await self._doc_repo.find_by_project_sorted(project_id, status=status_filter)

    async def get_doc(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, doc_id: uuid.UUID
    ) -> DocumentFile:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        return await self._get_doc_in_project_or_404(project_id, doc_id)

    async def create_doc(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        body: DocCreate,
        actor_user_id: uuid.UUID,
    ) -> DocumentFile:
        await self._project_service.get_project_or_404(tenant_id, project_id)

        existing = await self._doc_repo.find_by_path(project_id, body.path)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Document path already exists"
            )

        doc = DocumentFile(
            project_id=project_id,
            path=body.path,
            title=body.title,
            content=body.content,
            status=DocStatus.new,
            version=1,
            last_modified_by=actor_user_id,
        )
        await doc.insert()

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "doc.created",
            "document",
            doc.id,
            entity_label=doc.path,
            summary="created",
        )
        return doc

    async def update_doc(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        doc_id: uuid.UUID,
        body: DocUpdate,
        actor_user_id: uuid.UUID,
    ) -> DocumentFile:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        doc = await self._get_doc_in_project_or_404(project_id, doc_id)

        updates: dict[Any, Any] = {DocumentFile.last_modified_by: actor_user_id}
        if body.title is not None:
            updates[DocumentFile.title] = body.title
        if body.content is not None:
            updates[DocumentFile.content] = body.content
            updates[DocumentFile.version] = doc.version + 1
            updates[DocumentFile.status] = DocStatus.changed
        if body.status is not None:
            updates[DocumentFile.status] = body.status
        if body.path is not None:
            existing = await self._doc_repo.find_by_path(project_id, body.path)
            if existing is not None and existing.id != doc_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Path already in use"
                )
            updates[DocumentFile.path] = body.path

        await doc.set(updates)

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "doc.updated",
            "document",
            doc.id,
            entity_label=doc.path,
            summary="updated",
        )
        reloaded = await self._doc_repo.find_by_id(doc_id)
        assert reloaded is not None, "document vanished during update"
        return reloaded

    async def delete_doc(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        doc_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> None:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        doc = await self._get_doc_in_project_or_404(project_id, doc_id)

        await doc.set({DocumentFile.status: DocStatus.deleted})

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "doc.deleted",
            "document",
            doc.id,
            entity_label=doc.path,
            summary="deleted",
        )

    async def bulk_upsert(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        body: DocBulkRequest,
        actor_user_id: uuid.UUID,
    ) -> DocBulkResponse:
        """Upsert a batch of documents from the web UI.

        New docs get status `new`; existing docs bump version, flip status to
        `changed` and record the last modifier.
        """
        await self._project_service.get_project_or_404(tenant_id, project_id)

        created = 0
        updated = 0
        docs: list[DocumentFile] = []

        # Batch fetch existing docs by path
        paths = [item.path for item in body.documents]
        existing_map = await self._doc_repo.find_by_paths(project_id, paths)

        for item in body.documents:
            existing = existing_map.get(item.path)

            if existing is not None:
                await existing.set(
                    {
                        DocumentFile.title: item.title,
                        DocumentFile.content: item.content,
                        DocumentFile.version: existing.version + 1,
                        DocumentFile.status: DocStatus.changed,
                        DocumentFile.last_modified_by: actor_user_id,
                    }
                )
                # Re-fetch to get updated state
                refreshed = await self._doc_repo.find_by_id(existing.id)
                assert refreshed is not None, "document vanished during bulk upsert"
                docs.append(refreshed)
                updated += 1
            else:
                doc = DocumentFile(
                    project_id=project_id,
                    path=item.path,
                    title=item.title,
                    content=item.content,
                    status=DocStatus.new,
                    version=1,
                    last_modified_by=actor_user_id,
                )
                await doc.insert()
                docs.append(doc)
                created += 1

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "doc.bulk_upsert",
            "document",
            None,
            summary=f"bulk upsert: {created} created, {updated} updated",
            details={"created": created, "updated": updated},
        )
        return DocBulkResponse(
            created=created,
            updated=updated,
            documents=[DocResponse.model_validate(d) for d in docs],
        )
