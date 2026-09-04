"""CLI sync domain service (sdd CLI pull/push flows).

Encapsulates the data access behind the /cli/* endpoints. Wired by the
composition root like every other service.
"""

import uuid
from typing import Any

from fastapi import HTTPException, status

from app.models.base import utcnow
from app.models.bug import Bug, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.document_file import DocStatus, DocumentFile
from app.models.project import Project
from app.repositories import (
    BugRepository,
    ChangeRequestRepository,
    DocumentFileRepository,
)
from app.schemas.bugs import BugBulkItem
from app.schemas.change_requests import CRBulkItem
from app.schemas.docs import DocBulkItem
from app.services.numbering import NumberingService
from app.services.project_reset import ProjectResetService
from app.services.slug import parse_path_prefix  # noqa: F401  (re-exported for CLI path parsing)


class SyncService:
    def __init__(
        self,
        cr_repo: ChangeRequestRepository,
        bug_repo: BugRepository,
        doc_repo: DocumentFileRepository,
        numbering_service: NumberingService,
        reset_service: ProjectResetService,
    ) -> None:
        self._cr_repo = cr_repo
        self._bug_repo = bug_repo
        self._doc_repo = doc_repo
        self._numbering_service = numbering_service
        self._reset_service = reset_service

    # ── Pull (read) endpoints ────────────────────────────────────────────────

    async def pending_crs(self, project_id: uuid.UUID) -> list[ChangeRequest]:
        return await self._cr_repo.find_by_statuses(
            project_id,
            [CRStatus.draft, CRStatus.pending, CRStatus.approved],
        )

    async def open_bugs(self, project_id: uuid.UUID) -> list[Bug]:
        return await self._bug_repo.find_by_statuses(
            project_id,
            [BugStatus.draft, BugStatus.open, BugStatus.in_progress],
        )

    async def deleted_cr_ids(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        """IDs of CRs with status `deleted` in the project."""
        return await self._cr_repo.find_ids_by_status(project_id, CRStatus.deleted)

    async def deleted_bug_ids(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        """IDs of bugs with status `deleted` in the project."""
        return await self._bug_repo.find_ids_by_status(project_id, BugStatus.deleted)

    async def deleted_doc_ids(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        """IDs of documents with status `deleted` in the project."""
        return await self._doc_repo.find_ids_by_status(project_id, DocStatus.deleted)

    async def pull_docs(self, project_id: uuid.UUID) -> list[DocumentFile]:
        """All non-deleted project documents, sorted by path."""
        return await self._doc_repo.find_by_project_sorted(project_id, status=None)

    # ── Mark applied / resolved / enriched ───────────────────────────────────

    async def mark_cr_applied(self, cr_id: uuid.UUID, project_id: uuid.UUID) -> ChangeRequest:
        cr = await self._cr_repo.find_by_id(cr_id)
        if cr is None or cr.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found"
            )

        await cr.set(
            {
                ChangeRequest.status: CRStatus.applied,
                ChangeRequest.closed_at: utcnow(),
            }
        )
        reloaded = await self._cr_repo.find_by_id(cr_id)
        assert reloaded is not None, "change request vanished after update"
        return reloaded

    async def mark_bug_resolved(self, bug_id: uuid.UUID, project_id: uuid.UUID) -> Bug:
        bug = await self._bug_repo.find_by_id(bug_id)
        if bug is None or bug.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

        await bug.set(
            {
                Bug.status: BugStatus.resolved,
                Bug.closed_at: utcnow(),
            }
        )
        reloaded = await self._bug_repo.find_by_id(bug_id)
        assert reloaded is not None, "bug vanished after update"
        return reloaded

    async def mark_doc_enriched(
        self, doc_id: uuid.UUID, project_id: uuid.UUID, content: str
    ) -> DocumentFile:
        doc = await self._doc_repo.find_by_id(doc_id)
        if doc is None or doc.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        await doc.set(
            {
                DocumentFile.content: content,
                DocumentFile.status: DocStatus.new,
                DocumentFile.version: doc.version + 1,
            }
        )
        reloaded = await self._doc_repo.find_by_id(doc_id)
        assert reloaded is not None, "document vanished after update"
        return reloaded

    async def mark_cr_enriched(
        self, cr_id: uuid.UUID, project_id: uuid.UUID, body: str
    ) -> ChangeRequest:
        cr = await self._cr_repo.find_by_id(cr_id)
        if cr is None or cr.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found"
            )

        await cr.set(
            {
                ChangeRequest.body: body,
                ChangeRequest.status: CRStatus.pending,
            }
        )
        reloaded = await self._cr_repo.find_by_id(cr_id)
        assert reloaded is not None, "change request vanished after update"
        return reloaded

    async def mark_bug_enriched(self, bug_id: uuid.UUID, project_id: uuid.UUID, body: str) -> Bug:
        bug = await self._bug_repo.find_by_id(bug_id)
        if bug is None or bug.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

        await bug.set(
            {
                Bug.body: body,
                Bug.status: BugStatus.open,
            }
        )
        reloaded = await self._bug_repo.find_by_id(bug_id)
        assert reloaded is not None, "bug vanished after update"
        return reloaded

    # ── Push flows ────────────────────────────────────────────────────────────

    async def push_docs(
        self, project_id: uuid.UUID, documents: list[DocBulkItem]
    ) -> tuple[int, int, list[DocumentFile]]:
        """Upsert documents from the CLI; explicit status wins, default is `synced`."""
        created = 0
        updated = 0
        docs: list[DocumentFile] = []

        # Batch fetch existing docs by path
        paths = [item.path for item in documents]
        existing_map = await self._doc_repo.find_by_paths(project_id, paths)

        for item in documents:
            existing = existing_map.get(item.path)

            if existing is not None:
                await existing.set(
                    {
                        DocumentFile.title: item.title,
                        DocumentFile.content: item.content,
                        DocumentFile.version: existing.version + 1,
                        DocumentFile.status: item.status or DocStatus.synced,
                    }
                )
                refreshed = await self._doc_repo.find_by_id(existing.id)
                assert refreshed is not None, "document vanished during push"
                docs.append(refreshed)
                updated += 1
            else:
                doc = DocumentFile(
                    project_id=project_id,
                    path=item.path,
                    title=item.title,
                    content=item.content,
                    status=item.status or DocStatus.synced,
                    version=1,
                )
                await doc.insert()
                docs.append(doc)
                created += 1

        return created, updated, docs

    async def push_crs(
        self,
        project_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        items: list[CRBulkItem],
    ) -> tuple[int, int, list[ChangeRequest]]:
        """Upsert CRs from the CLI by id, with path fallback for stale IDs."""
        created = 0
        updated = 0
        crs: list[ChangeRequest] = []

        # Batch fetch existing CRs by id
        ids_to_fetch = [item.id for item in items if item.id is not None]
        existing_by_id: dict[uuid.UUID, ChangeRequest] = {}
        if ids_to_fetch:
            existing_by_id = await self._cr_repo.find_by_ids_in_project(project_id, ids_to_fetch)

        # Batch fetch by path as fallback for stale IDs (e.g. after external reset)
        stale_id_paths = [
            item.path
            for item in items
            if item.id is not None and existing_by_id.get(item.id) is None
        ]
        existing_by_path: dict[str, ChangeRequest] = {}
        if stale_id_paths:
            existing_by_path = await self._cr_repo.find_by_paths_batch(project_id, stale_id_paths)

        for item in items:
            existing = existing_by_id.get(item.id) if item.id else None
            if existing is None and item.id is not None:
                existing = existing_by_path.get(item.path)

            if existing is not None:
                updates: dict[Any, Any] = {}
                updates[ChangeRequest.path] = item.path
                updates[ChangeRequest.title] = item.title
                updates[ChangeRequest.body] = item.body
                if item.status is not None:
                    updates[ChangeRequest.status] = item.status
                if updates:
                    await existing.set(updates)
                refreshed = await self._cr_repo.find_by_id(existing.id)
                assert refreshed is not None, "change request vanished during push"
                crs.append(refreshed)
                updated += 1
            else:
                cr = ChangeRequest(
                    project_id=project_id,
                    number=0,
                    slug="",
                    path=item.path,
                    title=item.title,
                    body=item.body,
                    status=item.status or CRStatus.pending,
                    author_id=actor_user_id,
                )
                await self._numbering_service.assign_number_and_slug(
                    cr, project_id, item.title, item.path
                )
                crs.append(cr)
                created += 1

        return created, updated, crs

    async def push_bugs(
        self,
        project_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        items: list[BugBulkItem],
    ) -> tuple[int, int, list[Bug]]:
        """Upsert bugs from the CLI by id, with path fallback for stale IDs."""
        created = 0
        updated = 0
        bugs: list[Bug] = []

        # Batch fetch existing bugs by id
        ids_to_fetch = [item.id for item in items if item.id is not None]
        existing_by_id: dict[uuid.UUID, Bug] = {}
        if ids_to_fetch:
            existing_by_id = await self._bug_repo.find_by_ids_in_project(project_id, ids_to_fetch)

        # Batch fetch by path as fallback for stale IDs (e.g. after external reset)
        stale_id_paths = [
            item.path
            for item in items
            if item.id is not None and existing_by_id.get(item.id) is None
        ]
        existing_by_path: dict[str, Bug] = {}
        if stale_id_paths:
            existing_by_path = await self._bug_repo.find_by_paths_batch(project_id, stale_id_paths)

        for item in items:
            existing = existing_by_id.get(item.id) if item.id else None
            if existing is None and item.id is not None:
                existing = existing_by_path.get(item.path)

            if existing is not None:
                updates: dict[Any, Any] = {}
                updates[Bug.path] = item.path
                updates[Bug.title] = item.title
                updates[Bug.body] = item.body
                updates[Bug.severity] = item.severity
                if item.status is not None:
                    updates[Bug.status] = item.status
                if updates:
                    await existing.set(updates)
                refreshed = await self._bug_repo.find_by_id(existing.id)
                assert refreshed is not None, "bug vanished during push"
                bugs.append(refreshed)
                updated += 1
            else:
                bug = Bug(
                    project_id=project_id,
                    number=0,
                    slug="",
                    path=item.path,
                    title=item.title,
                    body=item.body,
                    status=item.status or BugStatus.draft,
                    severity=item.severity,
                    author_id=actor_user_id,
                )
                await self._numbering_service.assign_number_and_slug(
                    bug, project_id, item.title, item.path
                )
                bugs.append(bug)
                created += 1

        return created, updated, bugs

    # ── Delete flows ──────────────────────────────────────────────────────────

    async def delete_docs(self, project_id: uuid.UUID, paths: list[str]) -> tuple[int, list[str]]:
        deleted = 0
        deleted_paths: list[str] = []

        # Batch fetch existing docs by path
        existing_map = await self._doc_repo.find_by_paths(project_id, paths)

        for path in paths:
            doc = existing_map.get(path)
            if doc is not None and doc.status != DocStatus.deleted:
                await doc.set({DocumentFile.status: DocStatus.deleted})
                deleted += 1
                deleted_paths.append(path)

        return deleted, deleted_paths

    async def delete_crs(self, project_id: uuid.UUID, paths: list[str]) -> tuple[int, list[str]]:
        deleted = 0
        deleted_paths: list[str] = []

        for path in paths:
            cr = await self._cr_repo.find_one_by_path_active(project_id, path)
            if cr is not None:
                await cr.set(
                    {
                        ChangeRequest.status: CRStatus.deleted,
                        ChangeRequest.closed_at: utcnow(),
                    }
                )
                deleted += 1
                deleted_paths.append(path)

        return deleted, deleted_paths

    async def delete_bugs(self, project_id: uuid.UUID, paths: list[str]) -> tuple[int, list[str]]:
        deleted = 0
        deleted_paths: list[str] = []

        for path in paths:
            bug = await self._bug_repo.find_one_by_path_active(project_id, path)
            if bug is not None:
                await bug.set(
                    {
                        Bug.status: BugStatus.deleted,
                        Bug.closed_at: utcnow(),
                    }
                )
                deleted += 1
                deleted_paths.append(path)

        return deleted, deleted_paths

    # ── Reset ─────────────────────────────────────────────────────────────────

    async def reset_project(
        self, project: Project, confirm_slug: str, actor_user_id: uuid.UUID
    ) -> dict[str, Any]:
        if confirm_slug != project.slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slug mismatch: expected '{project.slug}'",
            )

        return await self._reset_service.reset_project_data(
            project, project.tenant_id, actor_user_id
        )
