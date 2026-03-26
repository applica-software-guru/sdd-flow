import asyncio
import json
import math
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member
from app.models.change_request import ChangeRequest
from app.models.bug import Bug
from app.models.project import Project
from app.models.tenant_member import TenantMember
from app.models.worker import Worker, WorkerStatus
from app.models.worker_job import JobStatus, JobType, WorkerJob
from app.models.worker_job_message import MessageKind, WorkerJobMessage
from app.schemas.workers import (
    WorkerJobAnswerRequest,
    WorkerJobCreate,
    WorkerJobDetail,
    WorkerJobListResponse,
    WorkerJobMessageResponse,
    WorkerJobResponse,
    WorkerResponse,
)
from app.services.worker_prompt import generate_worker_prompt

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}",
    tags=["workers"],
)

HEARTBEAT_TIMEOUT = timedelta(seconds=60)


async def _get_project(db: AsyncSession, tenant_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _is_online(worker: Worker) -> bool:
    if worker.last_heartbeat_at is None:
        return False
    return (datetime.now(timezone.utc) - worker.last_heartbeat_at) < HEARTBEAT_TIMEOUT


# --- Workers ---

@router.get("/workers", response_model=list[WorkerResponse])
async def list_workers(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(Worker).where(Worker.project_id == project_id).order_by(Worker.registered_at.desc())
    )
    workers = result.scalars().all()
    return [
        WorkerResponse(
            id=w.id,
            project_id=w.project_id,
            name=w.name,
            status=w.status,
            agent=w.agent,
            last_heartbeat_at=w.last_heartbeat_at,
            registered_at=w.registered_at,
            is_online=_is_online(w),
        )
        for w in workers
    ]


# --- Worker Jobs ---

@router.post("/worker-jobs", response_model=WorkerJobResponse, status_code=status.HTTP_201_CREATED)
async def create_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: WorkerJobCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)

    # Validate entity exists and status is appropriate for job_type
    from app.models.change_request import CRStatus
    from app.models.bug import BugStatus

    entity_title = None
    if body.entity_type == "change_request":
        result = await db.execute(
            select(ChangeRequest).where(
                ChangeRequest.id == body.entity_id,
                ChangeRequest.project_id == project_id,
            )
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
        entity_title = entity.title
        if body.job_type == JobType.enrich and entity.status != CRStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CR must be in 'draft' status to enrich")
        if body.job_type == JobType.apply and entity.status != CRStatus.approved:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CR must be in 'approved' status to apply")
    elif body.entity_type == "bug":
        result = await db.execute(
            select(Bug).where(Bug.id == body.entity_id, Bug.project_id == project_id)
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")
        entity_title = entity.title
        if body.job_type == JobType.enrich and entity.status != BugStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bug must be in 'draft' status to enrich")
        if body.job_type == JobType.apply and entity.status not in (BugStatus.open, BugStatus.in_progress):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bug must be in 'open' or 'in_progress' status to apply")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity_type")

    # Generate prompt
    prompt = await generate_worker_prompt(db, project_id, body.entity_type, body.entity_id, job_type=body.job_type.value)

    # Determine agent
    agent = body.agent
    if not agent:
        # Check if there's an online worker and use its agent
        worker_result = await db.execute(
            select(Worker).where(
                Worker.project_id == project_id,
                Worker.status.in_([WorkerStatus.online]),
            ).limit(1)
        )
        worker = worker_result.scalar_one_or_none()
        agent = worker.agent if worker else "claude"

    job = WorkerJob(
        project_id=project_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        job_type=body.job_type,
        status=JobStatus.queued,
        prompt=prompt,
        agent=agent,
        created_by=member.user_id,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    return WorkerJobResponse(
        id=job.id,
        project_id=job.project_id,
        worker_id=job.worker_id,
        worker_name=None,
        entity_type=job.entity_type,
        entity_id=job.entity_id,
        entity_title=entity_title,
        job_type=job.job_type,
        status=job.status,
        agent=job.agent,
        exit_code=job.exit_code,
        created_by=job.created_by,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/worker-jobs", response_model=WorkerJobListResponse)
async def list_worker_jobs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: JobStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)

    query = select(WorkerJob).where(WorkerJob.project_id == project_id)
    count_query = select(func.count()).select_from(WorkerJob).where(WorkerJob.project_id == project_id)

    if status_filter is not None:
        query = query.where(WorkerJob.status == status_filter)
        count_query = count_query.where(WorkerJob.status == status_filter)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(WorkerJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    jobs = result.scalars().all()

    # Enrich with worker names and entity titles
    items = []
    for job in jobs:
        worker_name = None
        if job.worker_id:
            w_result = await db.execute(select(Worker.name).where(Worker.id == job.worker_id))
            worker_name = w_result.scalar_one_or_none()

        entity_title = None
        if job.entity_type == "change_request":
            e_result = await db.execute(select(ChangeRequest.title).where(ChangeRequest.id == job.entity_id))
            entity_title = e_result.scalar_one_or_none()
        elif job.entity_type == "bug":
            e_result = await db.execute(select(Bug.title).where(Bug.id == job.entity_id))
            entity_title = e_result.scalar_one_or_none()

        items.append(WorkerJobResponse(
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
            exit_code=job.exit_code,
            created_by=job.created_by,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
            updated_at=job.updated_at,
        ))

    return WorkerJobListResponse(
        items=items,
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
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)

    result = await db.execute(
        select(WorkerJob).where(WorkerJob.id == job_id, WorkerJob.project_id == project_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Fetch messages
    msg_result = await db.execute(
        select(WorkerJobMessage).where(WorkerJobMessage.job_id == job_id)
        .order_by(WorkerJobMessage.sequence.asc())
    )
    messages = msg_result.scalars().all()

    # Enrich
    worker_name = None
    if job.worker_id:
        w_result = await db.execute(select(Worker.name).where(Worker.id == job.worker_id))
        worker_name = w_result.scalar_one_or_none()

    entity_title = None
    if job.entity_type == "change_request":
        e_result = await db.execute(select(ChangeRequest.title).where(ChangeRequest.id == job.entity_id))
        entity_title = e_result.scalar_one_or_none()
    elif job.entity_type == "bug":
        e_result = await db.execute(select(Bug.title).where(Bug.id == job.entity_id))
        entity_title = e_result.scalar_one_or_none()

    return WorkerJobDetail(
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
        exit_code=job.exit_code,
        created_by=job.created_by,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
        messages=[WorkerJobMessageResponse.model_validate(m) for m in messages],
    )


@router.get("/worker-jobs/{job_id}/stream")
async def stream_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint streaming job messages in real-time."""
    await _get_project(db, tenant_id, project_id)

    # Verify job exists
    result = await db.execute(
        select(WorkerJob).where(WorkerJob.id == job_id, WorkerJob.project_id == project_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    async def event_generator():
        last_sequence = 0
        while True:
            # Fetch new messages
            msg_result = await db.execute(
                select(WorkerJobMessage).where(
                    WorkerJobMessage.job_id == job_id,
                    WorkerJobMessage.sequence > last_sequence,
                ).order_by(WorkerJobMessage.sequence.asc())
            )
            messages = msg_result.scalars().all()

            for msg in messages:
                data = json.dumps({
                    "id": str(msg.id),
                    "job_id": str(msg.job_id),
                    "kind": msg.kind.value,
                    "content": msg.content,
                    "sequence": msg.sequence,
                    "created_at": msg.created_at.isoformat(),
                })
                yield f"data: {data}\n\n"
                last_sequence = msg.sequence

            # Check if job is done
            await db.refresh(job)
            if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
                done_data = json.dumps({"type": "done", "status": job.status.value, "exit_code": job.exit_code})
                yield f"event: done\ndata: {done_data}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
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
    db: AsyncSession = Depends(get_db),
):
    """User answers a question from the agent."""
    await _get_project(db, tenant_id, project_id)

    result = await db.execute(
        select(WorkerJob).where(WorkerJob.id == job_id, WorkerJob.project_id == project_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Get max sequence
    seq_result = await db.execute(
        select(WorkerJobMessage.sequence)
        .where(WorkerJobMessage.job_id == job_id)
        .order_by(WorkerJobMessage.sequence.desc())
        .limit(1)
    )
    max_seq = seq_result.scalar_one_or_none() or 0

    msg = WorkerJobMessage(
        job_id=job_id,
        kind=MessageKind.answer,
        content=body.content,
        sequence=max_seq + 1,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)

    return WorkerJobMessageResponse.model_validate(msg)


@router.post("/worker-jobs/{job_id}/cancel")
async def cancel_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a queued or running job."""
    await _get_project(db, tenant_id, project_id)

    result = await db.execute(
        select(WorkerJob).where(WorkerJob.id == job_id, WorkerJob.project_id == project_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status not in (JobStatus.queued, JobStatus.assigned, JobStatus.running):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in status '{job.status.value}'",
        )

    job.status = JobStatus.cancelled
    job.completed_at = datetime.now(timezone.utc)
    await db.flush()

    return {"status": "cancelled"}
