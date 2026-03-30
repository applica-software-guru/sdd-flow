import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_tenant_member
from app.models.document_file import DocStatus, DocumentFile
from app.models.tenant_member import TenantMember
from app.repositories import DocumentFileRepository, ProjectRepository
from app.schemas.docs import DocBulkRequest, DocBulkResponse, DocCreate, DocResponse, DocUpdate
from app.services.audit import log_event

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/docs",
    tags=["docs"],
)


async def _get_project(tenant_id: uuid.UUID, project_id: uuid.UUID):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or project.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=list[DocResponse])
async def list_docs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    status_filter: DocStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)

    if status_filter is not None:
        query: dict = {"projectId": project_id, "status": status_filter.value}
    else:
        query = {"projectId": project_id, "status": {"$ne": DocStatus.deleted.value}}

    docs = await DocumentFile.find(query).sort([("path", 1)]).to_list()
    return docs


@router.get("/{doc_id}", response_model=DocResponse)
async def get_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    doc_repo = DocumentFileRepository()
    doc = await doc_repo.find_by_id(doc_id)
    if doc is None or doc.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("", response_model=DocResponse, status_code=status.HTTP_201_CREATED)
async def create_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DocCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    doc_repo = DocumentFileRepository()

    existing = await doc_repo.find_by_path(project_id, body.path)
    if existing is not None:
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
    await doc.insert()

    await log_event(tenant_id, member.user_id, "doc.created", "document", doc.id)
    return doc


@router.patch("/{doc_id}", response_model=DocResponse)
async def update_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: DocUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    doc_repo = DocumentFileRepository()
    doc = await doc_repo.find_by_id(doc_id)
    if doc is None or doc.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    updates: dict = {DocumentFile.last_modified_by: member.user_id}
    if body.title is not None:
        updates[DocumentFile.title] = body.title
    if body.content is not None:
        updates[DocumentFile.content] = body.content
        updates[DocumentFile.version] = doc.version + 1
        updates[DocumentFile.status] = DocStatus.changed
    if body.status is not None:
        updates[DocumentFile.status] = body.status

    await doc.set(updates)

    await log_event(tenant_id, member.user_id, "doc.updated", "document", doc.id)
    doc = await doc_repo.find_by_id(doc_id)
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    doc_repo = DocumentFileRepository()
    doc = await doc_repo.find_by_id(doc_id)
    if doc is None or doc.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await doc.set({DocumentFile.status: DocStatus.deleted})

    await log_event(tenant_id, member.user_id, "doc.deleted", "document", doc.id)


@router.post("/bulk", response_model=DocBulkResponse)
async def bulk_upsert(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DocBulkRequest,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    doc_repo = DocumentFileRepository()

    created = 0
    updated = 0
    docs = []

    # Batch fetch existing docs by path
    paths = [item.path for item in body.documents]
    existing_map = await doc_repo.find_by_paths(project_id, paths)

    for item in body.documents:
        existing = existing_map.get(item.path)

        if existing is not None:
            await existing.set({
                DocumentFile.title: item.title,
                DocumentFile.content: item.content,
                DocumentFile.version: existing.version + 1,
                DocumentFile.status: DocStatus.changed,
                DocumentFile.last_modified_by: member.user_id,
            })
            # Re-fetch to get updated state
            refreshed = await doc_repo.find_by_id(existing.id)
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
                last_modified_by=member.user_id,
            )
            await doc.insert()
            docs.append(doc)
            created += 1

    await log_event(
        tenant_id, member.user_id, "doc.bulk_upsert", "document", None,
        details={"created": created, "updated": updated},
    )
    return DocBulkResponse(
        created=created,
        updated=updated,
        documents=[DocResponse.model_validate(d) for d in docs],
    )
