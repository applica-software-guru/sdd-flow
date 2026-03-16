import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member
from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.document_file import DocumentFile
from app.models.project import Project
from app.models.tenant_member import TenantMember
from app.schemas.search import SearchResponse, SearchResult

router = APIRouter(prefix="/tenants/{tenant_id}/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    tenant_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    pattern = f"%{q}%"
    results: list[SearchResult] = []

    # Search projects
    project_result = await db.execute(
        select(Project).where(
            Project.tenant_id == tenant_id,
            or_(Project.name.ilike(pattern), Project.description.ilike(pattern)),
        ).limit(10)
    )
    for p in project_result.scalars().all():
        results.append(SearchResult(
            entity_type="project",
            entity_id=p.id,
            title=p.name,
            snippet=p.description[:200] if p.description else None,
            project_id=p.id,
        ))

    # Search documents across tenant projects
    doc_result = await db.execute(
        select(DocumentFile)
        .join(Project, DocumentFile.project_id == Project.id)
        .where(
            Project.tenant_id == tenant_id,
            or_(DocumentFile.title.ilike(pattern), DocumentFile.content.ilike(pattern)),
        ).limit(10)
    )
    for d in doc_result.scalars().all():
        snippet = d.content[:200] if d.content else None
        results.append(SearchResult(
            entity_type="document",
            entity_id=d.id,
            title=d.title,
            snippet=snippet,
            project_id=d.project_id,
        ))

    # Search change requests
    cr_result = await db.execute(
        select(ChangeRequest)
        .join(Project, ChangeRequest.project_id == Project.id)
        .where(
            Project.tenant_id == tenant_id,
            or_(ChangeRequest.title.ilike(pattern), ChangeRequest.body.ilike(pattern)),
        ).limit(10)
    )
    for cr in cr_result.scalars().all():
        results.append(SearchResult(
            entity_type="change_request",
            entity_id=cr.id,
            title=cr.title,
            snippet=cr.body[:200] if cr.body else None,
            project_id=cr.project_id,
        ))

    # Search bugs
    bug_result = await db.execute(
        select(Bug)
        .join(Project, Bug.project_id == Project.id)
        .where(
            Project.tenant_id == tenant_id,
            or_(Bug.title.ilike(pattern), Bug.body.ilike(pattern)),
        ).limit(10)
    )
    for b in bug_result.scalars().all():
        results.append(SearchResult(
            entity_type="bug",
            entity_id=b.id,
            title=b.title,
            snippet=b.body[:200] if b.body else None,
            project_id=b.project_id,
        ))

    return SearchResponse(results=results, total=len(results), query=q)
