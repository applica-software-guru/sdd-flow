import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import ApiKeyContext, get_api_key_context, get_api_key_project
from app.models.bug import Bug, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.document_file import DocumentFile, DocStatus
from app.models.worker import Worker, WorkerStatus
from app.models.worker_job import JobStatus, JobType, WorkerJob
from app.models.worker_job_message import MessageKind, WorkerJobMessage
from app.schemas.workers import (
    WorkerHeartbeatRequest,
    WorkerJobAssignment,
    WorkerJobCompletedRequest,
    WorkerJobOutputRequest,
    WorkerJobQuestionRequest,
    WorkerJobMessageResponse,
    WorkerRegisterRequest,
    WorkerResponse,
)
from app.services.notifications import create_notification

router = APIRouter(prefix="/cli/workers", tags=["cli-workers"])

HEARTBEAT_TIMEOUT = timedelta(seconds=60)
STALE_JOB_TIMEOUT = timedelta(minutes=5)
POLL_DURATION = 30  # seconds
POLL_INTERVAL = 1  # seconds


async def _cleanup_stale_workers(db: AsyncSession, project_id: uuid.UUID) -> None:
    """Mark workers as offline if heartbeat is stale, and fail their running jobs."""
    cutoff = datetime.now(timezone.utc) - HEARTBEAT_TIMEOUT
    stale_job_cutoff = datetime.now(timezone.utc) - STALE_JOB_TIMEOUT

    await db.execute(
        update(Worker).where(
            Worker.project_id == project_id,
            Worker.status != WorkerStatus.offline,
            Worker.last_heartbeat_at < cutoff,
        ).values(status=WorkerStatus.offline)
    )

    stale_workers_sq = select(Worker.id).where(
        Worker.project_id == project_id,
        Worker.status == WorkerStatus.offline,
        Worker.last_heartbeat_at < stale_job_cutoff,
    )
    await db.execute(
        update(WorkerJob).where(
            WorkerJob.project_id == project_id,
            WorkerJob.status.in_([JobStatus.assigned, JobStatus.running]),
            WorkerJob.worker_id.in_(stale_workers_sq),
        ).values(
            status=JobStatus.failed,
            completed_at=datetime.now(timezone.utc),
        )
    )


@router.post("/register", response_model=WorkerResponse)
async def register_worker(
    body: WorkerRegisterRequest,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Register or reconnect a worker. Upserts by (project_id, name)."""
    result = await db.execute(
        select(Worker).where(
            Worker.project_id == project.id,
            Worker.name == body.name,
        )
    )
    worker = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if worker is not None:
        worker.status = WorkerStatus.online
        worker.agent = body.agent
        worker.branch = body.branch
        worker.last_heartbeat_at = now
        worker.metadata_ = body.metadata
    else:
        worker = Worker(
            project_id=project.id,
            name=body.name,
            status=WorkerStatus.online,
            agent=body.agent,
            branch=body.branch,
            last_heartbeat_at=now,
            metadata_=body.metadata,
        )
        db.add(worker)

    await db.flush()
    await db.refresh(worker)

    return WorkerResponse(
        id=worker.id,
        project_id=worker.project_id,
        name=worker.name,
        status=worker.status,
        agent=worker.agent,
        branch=worker.branch,
        last_heartbeat_at=worker.last_heartbeat_at,
        registered_at=worker.registered_at,
        is_online=True,
    )


@router.post("/{worker_id}/heartbeat")
async def heartbeat(
    worker_id: uuid.UUID,
    body: WorkerHeartbeatRequest,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Update worker heartbeat and status."""
    result = await db.execute(
        select(Worker).where(
            Worker.id == worker_id,
            Worker.project_id == project.id,
        )
    )
    worker = result.scalar_one_or_none()
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker.status = body.status
    worker.last_heartbeat_at = datetime.now(timezone.utc)
    await db.flush()

    await _cleanup_stale_workers(db, project.id)

    return {"status": "ok"}


@router.get("/{worker_id}/poll")
async def poll_job(
    worker_id: uuid.UUID,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Long-poll for a queued job. Holds connection up to 30s."""
    result = await db.execute(
        select(Worker).where(
            Worker.id == worker_id,
            Worker.project_id == project.id,
        )
    )
    worker = result.scalar_one_or_none()
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    await _cleanup_stale_workers(db, project.id)

    for _ in range(POLL_DURATION):
        job_result = await db.execute(
            select(WorkerJob).where(
                WorkerJob.project_id == project.id,
                WorkerJob.status == JobStatus.queued,
            ).order_by(WorkerJob.created_at.asc()).limit(1).with_for_update(skip_locked=True)
        )
        job = job_result.scalar_one_or_none()

        if job is not None:
            job.status = JobStatus.assigned
            job.worker_id = worker_id
            worker.status = WorkerStatus.busy
            worker.last_heartbeat_at = datetime.now(timezone.utc)
            await db.flush()
            await db.refresh(job)

            return WorkerJobAssignment(
                job_id=job.id,
                entity_type=job.entity_type,
                entity_id=job.entity_id,
                job_type=job.job_type,
                prompt=job.prompt,
                agent=job.agent,
                model=job.model,
                branch=worker.branch,
            )

        await db.commit()
        await asyncio.sleep(POLL_INTERVAL)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/jobs/{job_id}/started")
async def job_started(
    job_id: uuid.UUID,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Worker notifies that the agent process has started."""
    result = await db.execute(
        select(WorkerJob).where(
            WorkerJob.id == job_id,
            WorkerJob.project_id == project.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job.status = JobStatus.running
    job.started_at = datetime.now(timezone.utc)
    await db.flush()
    return {"status": "ok"}


@router.post("/jobs/{job_id}/output")
async def job_output(
    job_id: uuid.UUID,
    body: WorkerJobOutputRequest,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Worker posts batched output lines."""
    result = await db.execute(
        select(WorkerJobMessage.sequence)
        .where(WorkerJobMessage.job_id == job_id)
        .order_by(WorkerJobMessage.sequence.desc())
        .limit(1)
    )
    max_seq = result.scalar_one_or_none() or 0

    for i, line in enumerate(body.lines):
        msg = WorkerJobMessage(
            job_id=job_id,
            kind=MessageKind.output,
            content=line,
            sequence=max_seq + i + 1,
        )
        db.add(msg)

    await db.flush()
    return {"status": "ok", "count": len(body.lines)}


@router.post("/jobs/{job_id}/question")
async def job_question(
    job_id: uuid.UUID,
    body: WorkerJobQuestionRequest,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Worker posts a question from the agent."""
    result = await db.execute(
        select(WorkerJobMessage.sequence)
        .where(WorkerJobMessage.job_id == job_id)
        .order_by(WorkerJobMessage.sequence.desc())
        .limit(1)
    )
    max_seq = result.scalar_one_or_none() or 0

    msg = WorkerJobMessage(
        job_id=job_id,
        kind=MessageKind.question,
        content=body.content,
        sequence=max_seq + 1,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)

    # Notify the job creator
    job_result = await db.execute(
        select(WorkerJob).where(WorkerJob.id == job_id, WorkerJob.project_id == project.id)
    )
    job = job_result.scalar_one_or_none()
    if job:
        await create_notification(
            db=db,
            user_id=job.created_by,
            tenant_id=project.tenant_id,
            event_type="worker_question",
            entity_type="worker_job",
            entity_id=job_id,
            title=f"Worker needs your attention on job #{str(job_id)[:8]}",
        )

    return WorkerJobMessageResponse.model_validate(msg)


@router.get("/jobs/{job_id}/answers", response_model=list[WorkerJobMessageResponse])
async def job_answers(
    job_id: uuid.UUID,
    after_sequence: int = 0,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Worker reads answers from the user (new answers since after_sequence)."""
    result = await db.execute(
        select(WorkerJobMessage).where(
            WorkerJobMessage.job_id == job_id,
            WorkerJobMessage.kind == MessageKind.answer,
            WorkerJobMessage.sequence > after_sequence,
        ).order_by(WorkerJobMessage.sequence.asc())
    )
    return result.scalars().all()


@router.post("/jobs/{job_id}/completed")
async def job_completed(
    job_id: uuid.UUID,
    body: WorkerJobCompletedRequest,
    project: "Project" = Depends(get_api_key_project),
    db: AsyncSession = Depends(get_db),
):
    """Worker reports job completion. Auto-transitions the entity on success."""
    result = await db.execute(
        select(WorkerJob).where(
            WorkerJob.id == job_id,
            WorkerJob.project_id == project.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    now = datetime.now(timezone.utc)
    job.exit_code = body.exit_code
    job.completed_at = now
    job.status = JobStatus.completed if body.exit_code == 0 else JobStatus.failed
    if body.changed_files:
        job.changed_files = [f.model_dump() for f in body.changed_files]

    # Set worker back to online
    if job.worker_id:
        worker_result = await db.execute(
            select(Worker).where(Worker.id == job.worker_id)
        )
        worker = worker_result.scalar_one_or_none()
        if worker:
            worker.status = WorkerStatus.online

    # Auto-transition entity on success
    if body.exit_code == 0:
        if job.entity_type == "change_request":
            cr_result = await db.execute(
                select(ChangeRequest).where(ChangeRequest.id == job.entity_id)
            )
            cr = cr_result.scalar_one_or_none()
            if cr and cr.status == CRStatus.draft:
                cr.status = CRStatus.pending

        elif job.entity_type == "document":
            doc_result = await db.execute(
                select(DocumentFile).where(DocumentFile.id == job.entity_id)
            )
            doc = doc_result.scalar_one_or_none()
            if doc and doc.status == DocStatus.draft:
                doc.status = DocStatus.new

    await db.flush()

    # Send notification to job creator
    event_type = "worker_job_completed" if body.exit_code == 0 else "worker_job_failed"
    status_label = "completed" if body.exit_code == 0 else "failed"
    await create_notification(
        db=db,
        user_id=job.created_by,
        tenant_id=project.tenant_id,
        event_type=event_type,
        entity_type="worker_job",
        entity_id=job_id,
        title=f"Worker job #{str(job_id)[:8]} {status_label}",
    )

    return {"status": job.status.value, "exit_code": body.exit_code}
