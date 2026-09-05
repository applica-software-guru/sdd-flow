"""Read-only global administration endpoints for platform SUPER_USER accounts."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import get_platform_admin_service
from app.middleware.auth import require_platform_role
from app.models.user import PlatformRole, User
from app.services.platform_admin import PlatformAdminService

router = APIRouter(prefix="/admin", tags=["platform_admin"])
SuperUser = Annotated[User, Depends(require_platform_role(PlatformRole.super_user))]
AdminService = Annotated[PlatformAdminService, Depends(get_platform_admin_service)]


class Page(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    pages: int


@router.get("/overview")
async def overview(user: SuperUser, service: AdminService) -> dict[str, Any]:
    return await service.overview(user)


@router.get("/users", response_model=Page)
async def users(
    user: SuperUser,
    service: AdminService,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
    platform_role: PlatformRole | None = None,
    email_verified: bool | None = None,
) -> dict[str, Any]:
    return await service.users(
        user,
        page=page,
        page_size=page_size,
        search=search,
        platform_role=platform_role,
        email_verified=email_verified,
    )


@router.get("/tenants", response_model=Page)
async def tenants(
    user: SuperUser,
    service: AdminService,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
) -> dict[str, Any]:
    return await service.tenants(user, page=page, page_size=page_size, search=search)


@router.get("/projects", response_model=Page)
async def projects(
    user: SuperUser,
    service: AdminService,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
    tenant_id: UUID | None = None,
    archived: bool | None = None,
) -> dict[str, Any]:
    return await service.projects(
        user,
        page=page,
        page_size=page_size,
        search=search,
        tenant_id=tenant_id,
        archived=archived,
    )


@router.get("/audit-log", response_model=Page)
async def audit_log(
    user: SuperUser,
    service: AdminService,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    event_type: str | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    project_id: UUID | None = None,
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
) -> dict[str, Any]:
    return await service.audit_log(
        user,
        page=page,
        page_size=page_size,
        event_type=event_type,
        user_id=user_id,
        tenant_id=tenant_id,
        project_id=project_id,
        from_dt=from_dt,
        to_dt=to_dt,
    )
