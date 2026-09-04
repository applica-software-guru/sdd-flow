import uuid

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_document_service
from app.middleware.auth import get_current_tenant_member
from app.models.document_file import DocStatus
from app.models.tenant_member import TenantMember
from app.schemas.docs import DocBulkRequest, DocBulkResponse, DocCreate, DocResponse, DocUpdate
from app.services.documents import DocumentService

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/docs",
    tags=["docs"],
)


@router.get("", response_model=list[DocResponse])
async def list_docs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    status_filter: DocStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
    svc: DocumentService = Depends(get_document_service),
) -> list[DocResponse]:
    docs = await svc.list_docs(tenant_id, project_id, status_filter=status_filter)
    return [DocResponse.model_validate(d) for d in docs]


@router.get("/{doc_id}", response_model=DocResponse)
async def get_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: DocumentService = Depends(get_document_service),
) -> DocResponse:
    return DocResponse.model_validate(await svc.get_doc(tenant_id, project_id, doc_id))


@router.post("", response_model=DocResponse, status_code=status.HTTP_201_CREATED)
async def create_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DocCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: DocumentService = Depends(get_document_service),
) -> DocResponse:
    return DocResponse.model_validate(
        await svc.create_doc(tenant_id, project_id, body, member.user_id)
    )


@router.patch("/{doc_id}", response_model=DocResponse)
async def update_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: DocUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: DocumentService = Depends(get_document_service),
) -> DocResponse:
    return DocResponse.model_validate(
        await svc.update_doc(tenant_id, project_id, doc_id, body, member.user_id)
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    doc_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: DocumentService = Depends(get_document_service),
) -> None:
    await svc.delete_doc(tenant_id, project_id, doc_id, member.user_id)


@router.post("/bulk", response_model=DocBulkResponse)
async def bulk_upsert(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: DocBulkRequest,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: DocumentService = Depends(get_document_service),
) -> DocBulkResponse:
    return await svc.bulk_upsert(tenant_id, project_id, body, member.user_id)
