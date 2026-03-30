import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.middleware.auth import ApiKeyContext, get_api_key_context, get_api_key_project
from app.models.bug import Bug, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.document_file import DocumentFile, DocStatus
from app.models.worker import Worker, WorkerStatus
from app.models.worker_job import JobStatus, WorkerJob
from app.models.worker_job_message import MessageKind, WorkerJobMessage
from app.models.base import utcnow
from app.repositories import WorkerRepository
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

POLL_DURATION = 30  # seconds
POLL_INTERVAL = 1  # seconds


@router.post("/register", response_model=WorkerResponse)
async def register_worker(
    body: WorkerRegisterRequest,
    project: "Project" = Depends(get_api_key_project),
):
    """Register or reconnect a worker. Upserts by (project_id, name)."""
    worker_repo = WorkerRepository()
    worker = await worker_repo.register_or_update(
        project_id=project.id,
        name=body.name,
        agent=body.agent,
        branch=body.branch,
        metadata=body.metadata or {},
    )

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
):
    """Update worker heartbeat and status."""
    worker = await Worker.get(str(worker_id))
    if worker is None or str(worker.project_id) != str(project.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    await worker.set({
        Worker.status: body.status,
        Worker.last_heartbeat_at: utcnow(),
    })

    return {"status": "ok"}


@router.get("/{worker_id}/poll")
async def poll_job(
    worker_id: uuid.UUID,
    project: "Project" = Depends(get_api_key_project),
):
    """Long-poll for a queued job. Holds connection up to 30s."""
    worker = await Worker.get(str(worker_id))
    if worker is None or str(worker.project_id) != str(project.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker_repo = WorkerRepository()

    for _ in range(POLL_DURATION):
        job = await worker_repo.assign_job(project.id, worker_id)
        if job is not None:
            await worker.set({
                Worker.status: WorkerStatus.busy,
                Worker.last_heartbeat_at: utcnow(),
            })
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

        await asyncio.sleep(POLL_INTERVAL)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/jobs/{job_id}/started")
async def job_started(
    job_id: uuid.UUID,
    project: "Project" = Depends(get_api_key_project),
):
    """Worker notifies that the agent process has started."""
    job = await WorkerJob.get(str(job_id))
    if job is None or str(job.project_id) != str(project.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    await job.set({
        WorkerJob.status: JobStatus.running,
        WorkerJob.started_at: utcnow(),
    })
    return {"status": "ok"}


@router.post("/jobs/{job_id}/output")
async def job_output(
    job_id: uuid.UUID,
    body: WorkerJobOutputRequest,
    project: "Project" = Depends(get_api_key_project),
):
    """Worker posts batched output lines."""
    worker_repo = WorkerRepository()
    existing_messages = await worker_repo.find_messages(job_id)
    max_seq = existing_messages[-1].sequence if existing_messages else 0

    for i, line in enumerate(body.lines):
        msg = WorkerJobMessage(
            job_id=job_id,
            kind=MessageKind.output,
            content=line,
            sequence=max_seq + i + 1,
        )
        await worker_repo.create_message(msg)

    return {"status": "ok", "count": len(body.lines)}


@router.post("/jobs/{job_id}/question")
async def job_question(
    job_id: uuid.UUID,
    body: WorkerJobQuestionRequest,
    project: "Project" = Depends(get_api_key_project),
):
    """Worker posts a question from the agent."""
    worker_repo = WorkerRepository()
    existing_messages = await worker_repo.find_messages(job_id)
    max_seq = existing_messages[-1].sequence if existing_messages else 0

    msg = WorkerJobMessage(
        job_id=job_id,
        kind=MessageKind.question,
        content=body.content,
        sequence=max_seq + 1,
    )
    await worker_repo.create_message(msg)

    # Notify the job creator
    job = await WorkerJob.get(str(job_id))
    if job and str(job.project_id) == str(project.id):
        await create_notification(
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
):
    """Worker reads answers from the user (new answers since after_sequence)."""
    messages = await WorkerJobMessage.find(
        {
            "jobId": job_id,
            "kind": MessageKind.answer.value,
            "sequence": {"$gt": after_sequence},
        }
    ).sort([("sequence", 1)]).to_list()
    return messages


@router.post("/jobs/{job_id}/completed")
async def job_completed(
    job_id: uuid.UUID,
    body: WorkerJobCompletedRequest,
    project: "Project" = Depends(get_api_key_project),
):
    """Worker reports job completion. Auto-transitions the entity on success."""
    job = await WorkerJob.get(str(job_id))
    if job is None or str(job.project_id) != str(project.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    now = utcnow()
    new_status = JobStatus.completed if body.exit_code == 0 else JobStatus.failed
    updates: dict = {
        WorkerJob.exit_code: body.exit_code,
        WorkerJob.completed_at: now,
        WorkerJob.status: new_status,
    }
    if body.changed_files:
        updates[WorkerJob.changed_files] = [f.model_dump() for f in body.changed_files]
    await job.set(updates)

    # Set worker back to online
    if job.worker_id:
        worker = await Worker.get(str(job.worker_id))
        if worker:
            await worker.set({Worker.status: WorkerStatus.online})

    # Auto-transition entity on success
    if body.exit_code == 0:
        if job.entity_type == "change_request" and job.entity_id:
            cr = await ChangeRequest.get(str(job.entity_id))
            if cr and cr.status == CRStatus.draft:
                await cr.set({ChangeRequest.status: CRStatus.pending})

        elif job.entity_type == "document" and job.entity_id:
            doc = await DocumentFile.get(str(job.entity_id))
            if doc and doc.status == DocStatus.draft:
                await doc.set({DocumentFile.status: DocStatus.new})

    # Send notification to job creator
    event_type = "worker_job_completed" if body.exit_code == 0 else "worker_job_failed"
    status_label = "completed" if body.exit_code == 0 else "failed"
    await create_notification(
        user_id=job.created_by,
        tenant_id=project.tenant_id,
        event_type=event_type,
        entity_type="worker_job",
        entity_id=job_id,
        title=f"Worker job #{str(job_id)[:8]} {status_label}",
    )

    return {"status": new_status.value, "exit_code": body.exit_code}
