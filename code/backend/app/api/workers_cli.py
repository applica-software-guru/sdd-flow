import uuid

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_worker_job_service
from app.middleware.auth import get_api_key_project
from app.models.project import Project
from app.schemas.workers import (
    WorkerHeartbeatRequest,
    WorkerJobAssignment,
    WorkerJobCompletedRequest,
    WorkerJobMessageResponse,
    WorkerJobOutputRequest,
    WorkerJobQuestionRequest,
    WorkerRegisterRequest,
    WorkerResponse,
)
from app.services.worker_jobs import WorkerJobService

router = APIRouter(prefix="/cli/workers", tags=["cli-workers"])

POLL_DURATION = 30  # seconds
POLL_INTERVAL = 1  # seconds


@router.post("/register", response_model=WorkerResponse)
async def register_worker(
    body: WorkerRegisterRequest,
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> WorkerResponse:
    """Register or reconnect a worker. Upserts by (project_id, name)."""
    worker = await svc.register_worker(project.id, body)
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
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> dict[str, str]:
    """Update worker heartbeat and status."""
    await svc.worker_heartbeat(worker_id, project.id, body.status)
    return {"status": "ok"}


@router.get("/{worker_id}/poll", response_model=None)
async def poll_job(
    worker_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> Response | WorkerJobAssignment:
    """Long-poll for a queued job. Holds connection up to 30s."""
    job, worker = await svc.poll_for_job(
        worker_id,
        project.id,
        poll_duration=POLL_DURATION,
        poll_interval=POLL_INTERVAL,
    )
    if job is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

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


@router.post("/jobs/{job_id}/started")
async def job_started(
    job_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> dict[str, str]:
    """Worker notifies that the agent process has started."""
    await svc.job_started(job_id, project.id)
    return {"status": "ok"}


@router.post("/jobs/{job_id}/output")
async def job_output(
    job_id: uuid.UUID,
    body: WorkerJobOutputRequest,
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> dict[str, str | int]:
    """Worker posts batched output lines."""
    count = await svc.job_output(job_id, body.lines)
    return {"status": "ok", "count": count}


@router.post("/jobs/{job_id}/question")
async def job_question(
    job_id: uuid.UUID,
    body: WorkerJobQuestionRequest,
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> WorkerJobMessageResponse:
    """Worker posts a question from the agent."""
    msg = await svc.job_question(job_id, body.content, project.id, project.tenant_id)
    return WorkerJobMessageResponse.model_validate(msg)


@router.get("/jobs/{job_id}/answers", response_model=list[WorkerJobMessageResponse])
async def job_answers(
    job_id: uuid.UUID,
    after_sequence: int = 0,
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> list[WorkerJobMessageResponse]:
    """Worker reads answers from the user (new answers since after_sequence)."""
    messages = await svc.job_answers(job_id, after_sequence=after_sequence)
    return [WorkerJobMessageResponse.model_validate(m) for m in messages]


@router.post("/jobs/{job_id}/completed")
async def job_completed(
    job_id: uuid.UUID,
    body: WorkerJobCompletedRequest,
    project: Project = Depends(get_api_key_project),
    svc: WorkerJobService = Depends(get_worker_job_service),
) -> dict[str, str | int]:
    """Worker reports job completion. Auto-transitions the entity on success."""
    new_status, exit_code = await svc.job_completed(
        job_id, body.exit_code, body.changed_files, project.id, project.tenant_id
    )
    return {"status": new_status.value, "exit_code": exit_code}
