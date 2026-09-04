"""Global search (Cmd+K) domain service."""

import json
import re
import uuid
from typing import Literal

from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.document_file import DocumentFile
from app.repositories import (
    AuditRepository,
    BugRepository,
    ChangeRequestRepository,
    DocumentFileRepository,
    ProjectRepository,
)
from app.schemas.search import SearchResponse, SearchResult

TypeFilter = Literal["project", "doc", "cr", "bug", "audit_log"]


class SearchService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        doc_repo: DocumentFileRepository,
        cr_repo: ChangeRequestRepository,
        bug_repo: BugRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._project_repo = project_repo
        self._doc_repo = doc_repo
        self._cr_repo = cr_repo
        self._bug_repo = bug_repo
        self._audit_repo = audit_repo

    async def search(
        self,
        tenant_id: uuid.UUID,
        q: str,
        type_filter: TypeFilter | None = None,
    ) -> SearchResponse:
        pattern = re.compile(re.escape(q), re.IGNORECASE)
        results: list[SearchResult] = []

        # Search projects
        if type_filter is None or type_filter == "project":
            projects = await self._project_repo.search_in_tenant(tenant_id, pattern, limit=10)
            for p in projects:
                results.append(
                    SearchResult(
                        entity_type="project",
                        entity_id=p.id,
                        title=p.name,
                        snippet=p.description[:200] if p.description else None,
                        project_id=p.id,
                    )
                )

        # Search documents, CRs and bugs across tenant projects
        if type_filter is None or type_filter == "doc":
            for d in await self._docs(tenant_id, pattern):
                snippet = d.content[:200] if d.content else None
                results.append(
                    SearchResult(
                        entity_type="document",
                        entity_id=d.id,
                        title=d.title,
                        snippet=snippet,
                        project_id=d.project_id,
                    )
                )

        if type_filter is None or type_filter == "cr":
            for cr in await self._crs(tenant_id, pattern):
                results.append(
                    SearchResult(
                        entity_type="change_request",
                        entity_id=cr.id,
                        title=cr.title,
                        snippet=cr.body[:200] if cr.body else None,
                        project_id=cr.project_id,
                    )
                )

        if type_filter is None or type_filter == "bug":
            for b in await self._bugs(tenant_id, pattern):
                results.append(
                    SearchResult(
                        entity_type="bug",
                        entity_id=b.id,
                        title=b.title,
                        snippet=b.body[:200] if b.body else None,
                        project_id=b.project_id,
                    )
                )

        # Search audit log entries (event_type only)
        if type_filter is None or type_filter == "audit_log":
            audit_entries = await self._audit_repo.find_by_event_type(tenant_id, pattern, limit=10)
            for a in audit_entries:
                snippet = json.dumps(a.details)[:200] if a.details else None
                results.append(
                    SearchResult(
                        entity_type="audit_log",
                        entity_id=a.id,
                        title=a.event_type,
                        snippet=snippet,
                        project_id=None,
                    )
                )

        return SearchResponse(results=results, total=len(results), query=q)

    async def _tenant_project_ids(self, tenant_id: uuid.UUID) -> list[uuid.UUID]:
        tenant_projects = await self._project_repo.find_by_tenant(tenant_id, include_archived=True)
        return [p.id for p in tenant_projects]

    async def _docs(self, tenant_id: uuid.UUID, pattern: re.Pattern[str]) -> list[DocumentFile]:
        project_ids = await self._tenant_project_ids(tenant_id)
        if not project_ids:
            return []
        return await self._doc_repo.search_in_projects(
            project_ids, ["title", "content"], pattern, limit=10
        )

    async def _crs(self, tenant_id: uuid.UUID, pattern: re.Pattern[str]) -> list[ChangeRequest]:
        project_ids = await self._tenant_project_ids(tenant_id)
        if not project_ids:
            return []
        return await self._cr_repo.search_in_projects(
            project_ids, ["title", "body"], pattern, limit=10
        )

    async def _bugs(self, tenant_id: uuid.UUID, pattern: re.Pattern[str]) -> list[Bug]:
        project_ids = await self._tenant_project_ids(tenant_id)
        if not project_ids:
            return []
        return await self._bug_repo.search_in_projects(
            project_ids, ["title", "body"], pattern, limit=10
        )
