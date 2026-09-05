import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DashboardWindowPreset = Literal["last_7_days", "last_30_days", "last_90_days"]


class TenantDashboardTenant(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class TenantDashboardWindow(BaseModel):
    preset: DashboardWindowPreset
    from_: datetime = Field(alias="from")
    to: datetime

    model_config = {"populate_by_name": True}


class TenantDashboardKpis(BaseModel):
    active_projects: int = 0
    archived_projects: int = 0
    documents_total: int = 0
    documents_synced: int = 0
    documents_pending: int = 0
    docs_sync_percentage: int = 0
    open_bugs: int = 0
    critical_bugs: int = 0
    major_bugs: int = 0
    active_crs: int = 0
    review_queue_crs: int = 0
    comments_in_window: int = 0
    distinct_commenters_in_window: int = 0
    activity_events_in_window: int = 0
    workers_online: int = 0
    workers_total: int = 0


class TenantDashboardProjectStats(BaseModel):
    documents_total: int = 0
    documents_synced: int = 0
    documents_pending: int = 0
    open_bugs: int = 0
    critical_bugs: int = 0
    major_bugs: int = 0
    active_crs: int = 0
    review_queue_crs: int = 0
    comments_in_window: int = 0
    distinct_commenters_in_window: int = 0
    activity_events_in_window: int = 0
    workers_online: int = 0
    workers_total: int = 0
    last_activity_at: datetime | None = None


class TenantDashboardProject(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    archived_at: datetime | None = None
    stats: TenantDashboardProjectStats


class TenantDashboardResponse(BaseModel):
    tenant: TenantDashboardTenant
    window: TenantDashboardWindow
    kpis: TenantDashboardKpis
    projects: list[TenantDashboardProject]
