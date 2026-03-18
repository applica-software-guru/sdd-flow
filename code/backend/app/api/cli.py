import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import ApiKeyContext, get_api_key_context, get_api_key_project
from app.models.bug import Bug, BugSeverity, BugStatus
from app.models.change_request import CRStatus, ChangeRequest
from app.models.document_file import DocStatus, DocumentFile
from app.models.project import Project
from app.schemas.bugs import BugBulkRequest, BugBulkResponse, BugEnrichRequest, BugResponse
from app.schemas.change_requests import CRBulkRequest, CRBulkResponse, CREnrichRequest, CRResponse
from app.schemas.docs import DocBulkRequest, DocBulkResponse, DocEnrichRequest, DocResponse

router = APIRouter(prefix="/cli", tags=["cli"])


@router.get("/pending-crs", response_model=list[CRResponse])
async def pending_crs(
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChangeRequest).where(
            ChangeRequest.project_id == project.id,
            ChangeRequest.status.in_([CRStatus.draft, CRStatus.pending, CRStatus.approved]),
        ).order_by(ChangeRequest.created_at.desc())
    )
    return result.scalars().all()


@router.get("/open-bugs", response_model=list[BugResponse])
async def open_bugs(
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bug).where(
            Bug.project_id == project.id,
            Bug.status.in_([BugStatus.draft, BugStatus.open, BugStatus.in_progress]),
        ).order_by(Bug.created_at.desc())
    )
    return result.scalars().all()


@router.post("/crs/{cr_id}/applied", response_model=CRResponse)
async def mark_cr_applied(
    cr_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChangeRequest).where(
            ChangeRequest.id == cr_id,
            ChangeRequest.project_id == project.id,
        )
    )
    cr = result.scalar_one_or_none()
    if cr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    cr.status = CRStatus.applied
    cr.closed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(cr)
    return cr


@router.post("/bugs/{bug_id}/resolved", response_model=BugResponse)
async def mark_bug_resolved(
    bug_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bug).where(Bug.id == bug_id, Bug.project_id == project.id)
    )
    bug = result.scalar_one_or_none()
    if bug is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    bug.status = BugStatus.resolved
    bug.closed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(bug)
    return bug


@router.post("/push-docs", response_model=DocBulkResponse)
async def push_docs(
    body: DocBulkRequest,
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    created = 0
    updated = 0
    docs = []

    for item in body.documents:
        result = await db.execute(
            select(DocumentFile).where(
                DocumentFile.project_id == project.id,
                DocumentFile.path == item.path,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.title = item.title
            existing.content = item.content
            existing.version += 1
            existing.status = DocStatus.synced
            docs.append(existing)
            updated += 1
        else:
            doc = DocumentFile(
                project_id=project.id,
                path=item.path,
                title=item.title,
                content=item.content,
                status=DocStatus.synced,
                version=1,
            )
            db.add(doc)
            docs.append(doc)
            created += 1

    await db.flush()
    for doc in docs:
        await db.refresh(doc)
    return DocBulkResponse(
        created=created,
        updated=updated,
        documents=[DocResponse.model_validate(d) for d in docs],
    )


@router.get("/pull-docs", response_model=list[DocResponse])
async def pull_docs(
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DocumentFile).where(
            DocumentFile.project_id == project.id,
            DocumentFile.status != DocStatus.deleted,
        ).order_by(DocumentFile.path)
    )
    return result.scalars().all()


@router.post("/docs/{doc_id}/enriched", response_model=DocResponse)
async def mark_doc_enriched(
    doc_id: uuid.UUID,
    body: DocEnrichRequest,
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DocumentFile).where(
            DocumentFile.id == doc_id,
            DocumentFile.project_id == project.id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.content = body.content
    doc.status = DocStatus.new
    doc.version += 1
    await db.flush()
    await db.refresh(doc)
    return doc


@router.post("/crs/{cr_id}/enriched", response_model=CRResponse)
async def mark_cr_enriched(
    cr_id: uuid.UUID,
    body: CREnrichRequest,
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChangeRequest).where(
            ChangeRequest.id == cr_id,
            ChangeRequest.project_id == project.id,
        )
    )
    cr = result.scalar_one_or_none()
    if cr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    cr.body = body.body
    cr.status = CRStatus.pending
    await db.flush()
    await db.refresh(cr)
    return cr


@router.post("/bugs/{bug_id}/enriched", response_model=BugResponse)
async def mark_bug_enriched(
    bug_id: uuid.UUID,
    body: BugEnrichRequest,
    project: Project = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bug).where(Bug.id == bug_id, Bug.project_id == project.id)
    )
    bug = result.scalar_one_or_none()
    if bug is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    bug.body = body.body
    bug.status = BugStatus.open
    await db.flush()
    await db.refresh(bug)
    return bug


@router.post("/push-crs", response_model=CRBulkResponse)
async def push_crs(
    body: CRBulkRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
    db: AsyncSession = Depends(get_db),
):
    created = 0
    updated = 0
    crs = []

    for item in body.change_requests:
        existing = None
        if item.id is not None:
            result = await db.execute(
                select(ChangeRequest).where(
                    ChangeRequest.id == item.id,
                    ChangeRequest.project_id == ctx.project.id,
                )
            )
            existing = result.scalar_one_or_none()

        if existing is not None:
            existing.title = item.title
            existing.body = item.body
            existing.status = CRStatus.pending
            crs.append(existing)
            updated += 1
        else:
            cr = ChangeRequest(
                project_id=ctx.project.id,
                title=item.title,
                body=item.body,
                status=CRStatus.pending,
                author_id=ctx.user_id,
            )
            db.add(cr)
            crs.append(cr)
            created += 1

    await db.flush()
    for cr in crs:
        await db.refresh(cr)
    return CRBulkResponse(
        created=created,
        updated=updated,
        change_requests=[CRResponse.model_validate(cr) for cr in crs],
    )


@router.post("/push-bugs", response_model=BugBulkResponse)
async def push_bugs(
    body: BugBulkRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
    db: AsyncSession = Depends(get_db),
):
    created = 0
    updated = 0
    bugs = []

    for item in body.bugs:
        existing = None
        if item.id is not None:
            result = await db.execute(
                select(Bug).where(
                    Bug.id == item.id,
                    Bug.project_id == ctx.project.id,
                )
            )
            existing = result.scalar_one_or_none()

        if existing is not None:
            existing.title = item.title
            existing.body = item.body
            existing.severity = item.severity
            bugs.append(existing)
            updated += 1
        else:
            bug = Bug(
                project_id=ctx.project.id,
                title=item.title,
                body=item.body,
                status=BugStatus.open,
                severity=item.severity,
                author_id=ctx.user_id,
            )
            db.add(bug)
            bugs.append(bug)
            created += 1

    await db.flush()
    for bug in bugs:
        await db.refresh(bug)
    return BugBulkResponse(
        created=created,
        updated=updated,
        bugs=[BugResponse.model_validate(bug) for bug in bugs],
    )
