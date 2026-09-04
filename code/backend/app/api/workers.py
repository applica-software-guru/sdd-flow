import math
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.dependencies import get_worker_job_service
from app.middleware.auth import get_current_tenant_member
from app.models.tenant_member import TenantMember
from app.models.worker_job import JobStatus, WorkerJob
from app.schemas.workers import (
    ChangedFile,
    WorkerJobAnswerRequest,
    WorkerJobCreate,
    WorkerJobDetail,
    WorkerJobListResponse,
    WorkerJobMessageResponse,
    WorkerJobPreviewRequest,
    WorkerJobPreviewResponse,
    WorkerJobResponse,
    WorkerResponse,
)
from app.services.agent_models import AGENT_MODELS
from app.services.worker_jobs import WorkerJobService, is_online

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}",
    tags=["workers"],
)


def _build_job_response(
    job: WorkerJob, worker_name: str | None, entity_title: str | None
) -> WorkerJobResponse:
    return WorkerJobResponse(
        id=job.id,
        project_id=job.project_id,
        worker_id=job.worker_id,
        worker_name=worker_name,
        entity_type=job.entity_type,
        entity_id=job.entity_id,
        entity_title=entity_title,
        job_type=job.job_type,
        status=job.status,
        agent=job.agent,
        model=job.model,
        exit_code=job.exit_code,
        created_by=job.created_by,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
        changed_files=[ChangedFile.model_validate(f) for f in job.changed_files],
    )


# --- Workers ---


@router.get("/workers", response_model=list[WorkerResponse])
async def list_workers(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> list[WorkerResponse]:
    workers = await svc.list_workers(tenant_id, project_id)
    return [
        WorkerResponse(
            id=w.id,
            project_id=w.project_id,
            name=w.name,
            status=w.status,
            agent=w.agent,
            branch=w.branch,
            last_heartbeat_at=w.last_heartbeat_at,
            registered_at=w.registered_at,
            is_online=is_online(w),
        )
        for w in workers
    ]


# --- Worker Jobs ---


@router.get("/worker-jobs/agent-models")
async def get_agent_models(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> dict[str, Any]:
    """Return available models per agent."""
    await svc.list_workers(tenant_id, project_id)  # project existence check
    return AGENT_MODELS


@router.post("/worker-jobs/preview", response_model=WorkerJobPreviewResponse)
async def preview_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: WorkerJobPreviewRequest,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> WorkerJobPreviewResponse:
    """Generate the prompt for a job without creating it."""
    prompt = await svc.preview_job(tenant_id, project_id, body)
    return WorkerJobPreviewResponse(prompt=prompt)


@router.post("/worker-jobs", response_model=WorkerJobResponse, status_code=status.HTTP_201_CREATED)
async def create_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: WorkerJobCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> WorkerJobResponse:
    job, entity_title = await svc.create_job(tenant_id, project_id, body, member.user_id)
    return _build_job_response(job, None, entity_title)


@router.get("/worker-jobs", response_model=WorkerJobListResponse)
async def list_worker_jobs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: JobStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> WorkerJobListResponse:
    items, total = await svc.list_jobs(
        tenant_id, project_id, page, page_size, status_filter=status_filter
    )
    return WorkerJobListResponse(
        items=[
            _build_job_response(job, worker_name, entity_title)
            for job, worker_name, entity_title in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/worker-jobs/{job_id}", response_model=WorkerJobDetail)
async def get_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> WorkerJobDetail:
    job, messages, worker_name, entity_title = await svc.get_job_with_detail(
        tenant_id, project_id, job_id
    )
    return WorkerJobDetail(
        **_build_job_response(job, worker_name, entity_title).model_dump(),
        messages=[WorkerJobMessageResponse.model_validate(m) for m in messages],
    )


@router.get("/worker-jobs/{job_id}/stream")
async def stream_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> StreamingResponse:
    """SSE endpoint streaming job messages in real-time."""
    return StreamingResponse(
        svc.stream_events(tenant_id, project_id, job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/worker-jobs/{job_id}/answer")
async def answer_question(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    body: WorkerJobAnswerRequest,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> WorkerJobMessageResponse:
    """User answers a question from the agent."""
    msg = await svc.answer_question(tenant_id, project_id, job_id, body.content)
    return WorkerJobMessageResponse.model_validate(msg)


@router.post("/worker-jobs/{job_id}/cancel")
async def cancel_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> dict[str, str]:
    """Cancel a queued or running job."""
    await svc.cancel_job(tenant_id, project_id, job_id)
    return {"status": "cancelled"}
