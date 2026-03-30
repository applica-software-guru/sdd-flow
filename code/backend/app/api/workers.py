import asyncio
import json
import math
import uuid
from datetime import datetime, timedelta, timezone

from app.utils.bson import uuid_to_bin
from bson.binary import Binary, UuidRepresentation
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.middleware.auth import get_current_tenant_member
from app.models.bug import Bug, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.document_file import DocumentFile, DocStatus
from app.models.tenant_member import TenantMember
from app.models.worker import Worker, WorkerStatus
from app.models.worker_job import JobStatus, JobType, WorkerJob
from app.models.worker_job_message import MessageKind, WorkerJobMessage
from app.repositories import ProjectRepository, WorkerRepository
from app.schemas.workers import (
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
from app.services.worker_prompt import generate_worker_prompt

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}",
    tags=["workers"],
)

HEARTBEAT_TIMEOUT = timedelta(seconds=60)




async def _get_project(tenant_id: uuid.UUID, project_id: uuid.UUID):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or project.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _is_online(worker: Worker) -> bool:
    if worker.last_heartbeat_at is None:
        return False
    return (datetime.now(timezone.utc) - worker.last_heartbeat_at) < HEARTBEAT_TIMEOUT


async def _validate_entity(
    project_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    job_type: JobType,
) -> str:
    """Validate entity exists and has correct status for the job type. Returns entity title."""
    if entity_type == "change_request":
        entity = await ChangeRequest.get(entity_id)
        if entity is None or entity.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
        if entity.status != CRStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CR must be in 'draft' status to enrich")
        return entity.title

    elif entity_type == "bug":
        entity = await Bug.get(entity_id)
        if entity is None or entity.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")
        if entity.status != BugStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bug must be in 'draft' status to enrich")
        return entity.title

    elif entity_type == "document":
        entity = await DocumentFile.get(entity_id)
        if entity is None or entity.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        if entity.status == DocStatus.deleted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot enrich a deleted document")
        return entity.title

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity_type")


async def _get_entity_title(entity_type: str | None, entity_id: uuid.UUID | None) -> str | None:
    if entity_type is None or entity_id is None:
        return None
    if entity_type == "change_request":
        cr = await ChangeRequest.get(entity_id)
        return cr.title if cr else None
    elif entity_type == "bug":
        bug = await Bug.get(entity_id)
        return bug.title if bug else None
    elif entity_type == "document":
        doc = await DocumentFile.get(entity_id)
        return doc.title if doc else None
    return None


def _build_job_response(job: WorkerJob, worker_name: str | None, entity_title: str | None) -> WorkerJobResponse:
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
        changed_files=job.changed_files,
    )


# --- Workers ---

@router.get("/workers", response_model=list[WorkerResponse])
async def list_workers(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    worker_repo = WorkerRepository()
    workers = await worker_repo.find_by_project(project_id)
    # Sort by registered_at desc
    workers = sorted(workers, key=lambda w: w.registered_at, reverse=True)
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
            is_online=_is_online(w),
        )
        for w in workers
    ]


# --- Worker Jobs ---

@router.get("/worker-jobs/agent-models")
async def get_agent_models(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    """Return available models per agent."""
    await _get_project(tenant_id, project_id)
    return AGENT_MODELS


@router.post("/worker-jobs/preview", response_model=WorkerJobPreviewResponse)
async def preview_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: WorkerJobPreviewRequest,
    member: TenantMember = Depends(get_current_tenant_member),
):
    """Generate the prompt for a job without creating it."""
    await _get_project(tenant_id, project_id)

    if body.job_type in (JobType.build, JobType.custom):
        # Project-level jobs — no entity required
        pass
    else:
        if body.entity_type is None or body.entity_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="entity_type and entity_id are required for enrich jobs",
            )
        await _validate_entity(project_id, body.entity_type, body.entity_id, body.job_type)

    if body.job_type == JobType.custom:
        return WorkerJobPreviewResponse(prompt="")

    prompt = await generate_worker_prompt(
        project_id, body.entity_type, body.entity_id, job_type=body.job_type.value
    )
    return WorkerJobPreviewResponse(prompt=prompt)


@router.post("/worker-jobs", response_model=WorkerJobResponse, status_code=status.HTTP_201_CREATED)
async def create_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: WorkerJobCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)

    entity_title = None
    worker_branch = None

    if body.job_type in (JobType.build, JobType.custom):
        # Project-level jobs — no entity required
        if body.job_type == JobType.custom and not body.prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="prompt is required for custom jobs",
            )
    else:
        if body.entity_type is None or body.entity_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="entity_type and entity_id are required for enrich jobs",
            )
        entity_title = await _validate_entity(project_id, body.entity_type, body.entity_id, body.job_type)

    # Resolve worker and its branch
    target_worker = None
    if body.worker_id:
        target_worker = await Worker.get(body.worker_id)
        if target_worker is None or target_worker.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
        worker_branch = target_worker.branch

    # Determine agent
    agent = body.agent
    if not agent:
        if target_worker:
            agent = target_worker.agent
        else:
            online_worker = await Worker.find_one(
                {"projectId": project_id, "status": WorkerStatus.online.value}
            )
            agent = online_worker.agent if online_worker else "claude"

    # Generate or use override prompt
    if body.prompt:
        prompt = body.prompt
    else:
        prompt = await generate_worker_prompt(
            project_id, body.entity_type, body.entity_id,
            job_type=body.job_type.value, branch=worker_branch,
        )

    job = WorkerJob(
        project_id=project_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        job_type=body.job_type,
        status=JobStatus.queued,
        prompt=prompt,
        agent=agent,
        model=body.model,
        created_by=member.user_id,
    )
    await job.insert()

    return _build_job_response(job, None, entity_title)


@router.get("/worker-jobs", response_model=WorkerJobListResponse)
async def list_worker_jobs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: JobStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)

    worker_repo = WorkerRepository()
    jobs, total = await worker_repo.find_jobs_by_project(
        project_id, status=status_filter, page=page, page_size=page_size
    )

    # Batch worker names
    worker_ids = list({j.worker_id for j in jobs if j.worker_id})
    workers_by_id: dict = {}
    if worker_ids:
        worker_id_bins = [uuid_to_bin(w) for w in worker_ids]
        workers = await Worker.find({"_id": {"$in": worker_id_bins}}).to_list()
        workers_by_id = {w.id: w.name for w in workers}

    # Batch entity titles by type
    cr_ids = [j.entity_id for j in jobs if j.entity_type == "change_request" and j.entity_id]
    bug_ids = [j.entity_id for j in jobs if j.entity_type == "bug" and j.entity_id]
    doc_ids = [j.entity_id for j in jobs if j.entity_type == "document" and j.entity_id]

    cr_titles: dict = {}
    bug_titles: dict = {}
    doc_titles: dict = {}

    if cr_ids:
        cr_id_bins = [uuid_to_bin(i) for i in cr_ids]
        crs = await ChangeRequest.find({"_id": {"$in": cr_id_bins}}).to_list()
        cr_titles = {cr.id: cr.title for cr in crs}

    if bug_ids:
        bug_id_bins = [uuid_to_bin(i) for i in bug_ids]
        bugs = await Bug.find({"_id": {"$in": bug_id_bins}}).to_list()
        bug_titles = {b.id: b.title for b in bugs}

    if doc_ids:
        doc_id_bins = [uuid_to_bin(i) for i in doc_ids]
        docs = await DocumentFile.find({"_id": {"$in": doc_id_bins}}).to_list()
        doc_titles = {d.id: d.title for d in docs}

    items = []
    for job in jobs:
        worker_name = workers_by_id.get(job.worker_id) if job.worker_id else None
        entity_title = None
        if job.entity_type == "change_request" and job.entity_id:
            entity_title = cr_titles.get(job.entity_id)
        elif job.entity_type == "bug" and job.entity_id:
            entity_title = bug_titles.get(job.entity_id)
        elif job.entity_type == "document" and job.entity_id:
            entity_title = doc_titles.get(job.entity_id)
        items.append(_build_job_response(job, worker_name, entity_title))

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
):
    await _get_project(tenant_id, project_id)

    worker_repo = WorkerRepository()
    job = await worker_repo.find_job_by_id(job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    messages = await worker_repo.find_messages(job_id)

    worker_name = None
    if job.worker_id:
        w = await Worker.get(job.worker_id)
        worker_name = w.name if w else None

    entity_title = await _get_entity_title(job.entity_type, job.entity_id)

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
):
    """SSE endpoint streaming job messages in real-time."""
    await _get_project(tenant_id, project_id)

    job = await WorkerJob.get(job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    async def event_generator():
        last_sequence = 0
        while True:
            messages = await WorkerJobMessage.find(
                {"jobId": job_id, "sequence": {"$gt": last_sequence}}
            ).sort([("sequence", 1)]).to_list()

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

            current_job = await WorkerJob.get(job_id)
            if current_job and current_job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
                done_data = json.dumps({"type": "done", "status": current_job.status.value, "exit_code": current_job.exit_code})
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
):
    """User answers a question from the agent."""
    await _get_project(tenant_id, project_id)

    worker_repo = WorkerRepository()
    job = await worker_repo.find_job_by_id(job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    messages = await worker_repo.find_messages(job_id)
    max_seq = messages[-1].sequence if messages else 0

    msg = WorkerJobMessage(
        job_id=job_id,
        kind=MessageKind.answer,
        content=body.content,
        sequence=max_seq + 1,
    )
    await worker_repo.create_message(msg)

    return WorkerJobMessageResponse.model_validate(msg)


@router.post("/worker-jobs/{job_id}/cancel")
async def cancel_worker_job(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    """Cancel a queued or running job."""
    await _get_project(tenant_id, project_id)

    worker_repo = WorkerRepository()
    job = await worker_repo.find_job_by_id(job_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status not in (JobStatus.queued, JobStatus.assigned, JobStatus.running):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in status '{job.status.value}'",
        )

    await job.set({
        WorkerJob.status: JobStatus.cancelled,
        WorkerJob.completed_at: datetime.now(timezone.utc),
    })

    return {"status": "cancelled"}
