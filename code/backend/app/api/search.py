import json
import re
import uuid
from typing import Literal

from app.utils.bson import uuid_to_bin
from bson.binary import Binary, UuidRepresentation
from fastapi import APIRouter, Depends, Query

from app.middleware.auth import get_current_tenant_member
from app.models.audit_log_entry import AuditLogEntry
from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.document_file import DocumentFile
from app.models.project import Project
from app.models.tenant_member import TenantMember
from app.schemas.search import SearchResponse, SearchResult

router = APIRouter(prefix="/tenants/{tenant_id}/search", tags=["search"])

TypeFilter = Literal["project", "doc", "cr", "bug", "audit_log"]




@router.get("", response_model=SearchResponse)
async def search(
    tenant_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    type: TypeFilter | None = Query(None),
    member: TenantMember = Depends(get_current_tenant_member),
):
    pattern = re.compile(re.escape(q), re.IGNORECASE)
    results: list[SearchResult] = []

    # Search projects
    if type is None or type == "project":
        projects = await Project.find(
            {
                "tenantId": tenant_id,
                "$or": [{"name": pattern}, {"description": pattern}],
            }
        ).limit(10).to_list()
        for p in projects:
            results.append(SearchResult(
                entity_type="project",
                entity_id=p.id,
                title=p.name,
                snippet=p.description[:200] if p.description else None,
                project_id=p.id,
            ))

    # Search documents across tenant projects
    if type is None or type == "doc":
        tenant_projects = await Project.find({"tenantId": tenant_id}).to_list()
        project_id_uuids = [p.id for p in tenant_projects]
        if project_id_uuids:
            project_id_bins = [uuid_to_bin(pid) for pid in project_id_uuids]
            docs = await DocumentFile.find(
                {
                    "projectId": {"$in": project_id_bins},
                    "$or": [{"title": pattern}, {"content": pattern}],
                }
            ).limit(10).to_list()
            for d in docs:
                snippet = d.content[:200] if d.content else None
                results.append(SearchResult(
                    entity_type="document",
                    entity_id=d.id,
                    title=d.title,
                    snippet=snippet,
                    project_id=d.project_id,
                ))

    # Search change requests
    if type is None or type == "cr":
        tenant_projects = await Project.find({"tenantId": tenant_id}).to_list()
        project_id_uuids = [p.id for p in tenant_projects]
        if project_id_uuids:
            project_id_bins = [uuid_to_bin(pid) for pid in project_id_uuids]
            crs = await ChangeRequest.find(
                {
                    "projectId": {"$in": project_id_bins},
                    "$or": [{"title": pattern}, {"body": pattern}],
                }
            ).limit(10).to_list()
            for cr in crs:
                results.append(SearchResult(
                    entity_type="change_request",
                    entity_id=cr.id,
                    title=cr.title,
                    snippet=cr.body[:200] if cr.body else None,
                    project_id=cr.project_id,
                ))

    # Search bugs
    if type is None or type == "bug":
        tenant_projects = await Project.find({"tenantId": tenant_id}).to_list()
        project_id_uuids = [p.id for p in tenant_projects]
        if project_id_uuids:
            project_id_bins = [uuid_to_bin(pid) for pid in project_id_uuids]
            bugs = await Bug.find(
                {
                    "projectId": {"$in": project_id_bins},
                    "$or": [{"title": pattern}, {"body": pattern}],
                }
            ).limit(10).to_list()
            for b in bugs:
                results.append(SearchResult(
                    entity_type="bug",
                    entity_id=b.id,
                    title=b.title,
                    snippet=b.body[:200] if b.body else None,
                    project_id=b.project_id,
                ))

    # Search audit log entries (event_type only)
    if type is None or type == "audit_log":
        audit_entries = await AuditLogEntry.find(
            {
                "tenantId": tenant_id,
                "eventType": pattern,
            }
        ).limit(10).to_list()
        for a in audit_entries:
            snippet = json.dumps(a.details)[:200] if a.details else None
            results.append(SearchResult(
                entity_type="audit_log",
                entity_id=a.id,
                title=a.event_type,
                snippet=snippet,
                project_id=None,
            ))

    return SearchResponse(results=results, total=len(results), query=q)
