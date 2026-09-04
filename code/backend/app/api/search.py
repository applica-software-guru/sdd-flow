import uuid

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_search_service
from app.middleware.auth import get_current_tenant_member
from app.models.tenant_member import TenantMember
from app.schemas.search import SearchResponse
from app.services.search import SearchService, TypeFilter

router = APIRouter(prefix="/tenants/{tenant_id}/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    tenant_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    type: TypeFilter | None = Query(None),
    member: TenantMember = Depends(get_current_tenant_member),
    svc: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return await svc.search(tenant_id, q, type_filter=type)
