import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member
from app.models.document_file import DocStatus, DocumentFile
from app.models.project import Project
from app.models.tenant_member import TenantMember
from app.schemas.docs import DocBulkRequest, DocBulkResponse, DocCreate, DocResponse, DocUpdate
from app.services.audit import log_event

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/docs",
    tags=["docs"],
)


async def _get_project(db: AsyncSession, tenant_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=list[DocResponse])
async def list_docs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(DocumentFile)
        .where(DocumentFile.project_id == project_id, DocumentFile.status != DocStatus.deleted)
        .order_by(DocumentFile.path)
    )
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocResponse)
async def get_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(DocumentFile).where(DocumentFile.id == doc_id, DocumentFile.project_id == project_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("", response_model=DocResponse, status_code=status.HTTP_201_CREATED)
async def create_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DocCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)

    result = await db.execute(
        select(DocumentFile).where(
            DocumentFile.project_id == project_id, DocumentFile.path == body.path
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document path already exists")

    doc = DocumentFile(
        project_id=project_id,
        path=body.path,
        title=body.title,
        content=body.content,
        status=DocStatus.new,
        version=1,
        last_modified_by=member.user_id,
    )
    db.add(doc)
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "doc.created", "document", doc.id)
    await db.refresh(doc)
    return doc


@router.patch("/{doc_id}", response_model=DocResponse)
async def update_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: DocUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(DocumentFile).where(DocumentFile.id == doc_id, DocumentFile.project_id == project_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if body.title is not None:
        doc.title = body.title
    if body.content is not None:
        doc.content = body.content
        doc.version += 1
        doc.status = DocStatus.changed
    if body.status is not None:
        doc.status = body.status
    doc.last_modified_by = member.user_id
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "doc.updated", "document", doc.id)
    await db.refresh(doc)
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(DocumentFile).where(DocumentFile.id == doc_id, DocumentFile.project_id == project_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.status = DocStatus.deleted
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "doc.deleted", "document", doc.id)


@router.post("/bulk", response_model=DocBulkResponse)
async def bulk_upsert(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DocBulkRequest,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)

    created = 0
    updated = 0
    docs = []

    for item in body.documents:
        result = await db.execute(
            select(DocumentFile).where(
                DocumentFile.project_id == project_id, DocumentFile.path == item.path
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.title = item.title
            existing.content = item.content
            existing.version += 1
            existing.status = DocStatus.changed
            existing.last_modified_by = member.user_id
            docs.append(existing)
            updated += 1
        else:
            doc = DocumentFile(
                project_id=project_id,
                path=item.path,
                title=item.title,
                content=item.content,
                status=DocStatus.new,
                version=1,
                last_modified_by=member.user_id,
            )
            db.add(doc)
            docs.append(doc)
            created += 1

    await db.flush()

    for d in docs:
        await db.refresh(d)

    await log_event(
        db, tenant_id, member.user_id, "doc.bulk_upsert", "document", None,
        details={"created": created, "updated": updated},
    )
    return DocBulkResponse(
        created=created,
        updated=updated,
        documents=[DocResponse.model_validate(d) for d in docs],
    )
