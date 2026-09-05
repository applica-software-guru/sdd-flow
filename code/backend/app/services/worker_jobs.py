"""Worker / worker-job domain service.

Covers both the web routes (create/preview/stream jobs, answer questions,
cancel) and the CLI daemon protocol (register, heartbeat, poll, output,
question, answers, completed with entity auto-transition). Also generates
agent prompts (absorbed from the former worker_prompt module).
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.models.base import utcnow
from app.models.bug import BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.document_file import DocStatus, DocumentFile
from app.models.user import User
from app.models.worker import Worker, WorkerStatus
from app.models.worker_job import JobStatus, JobType, WorkerJob
from app.models.worker_job_message import MessageKind, WorkerJobMessage
from app.repositories import (
    BugRepository,
    ChangeRequestRepository,
    CommentRepository,
    DocumentFileRepository,
    WorkerRepository,
)
from app.schemas.workers import (
    ChangedFile,
    WorkerJobCreate,
    WorkerJobPreviewRequest,
    WorkerRegisterRequest,
)
from app.services.notifications import NotificationService
from app.services.projects import ProjectService

HEARTBEAT_TIMEOUT = timedelta(seconds=60)

_REPORT_SECTION = (
    "\n\n---\n\n"
    "## Report\n\n"
    "At the end of your work, provide a detailed report including:\n"
    "- What was done (files created, modified, enriched)\n"
    "- Actions taken for each item\n"
    "- Any issues encountered or decisions made"
)


def is_online(worker: Worker) -> bool:
    # last_heartbeat_at is non-optional (default_factory=utcnow)
    return (datetime.now(UTC) - worker.last_heartbeat_at) < HEARTBEAT_TIMEOUT


class WorkerJobService:
    def __init__(
        self,
        project_service: ProjectService,
        worker_repo: WorkerRepository,
        cr_repo: ChangeRequestRepository,
        bug_repo: BugRepository,
        doc_repo: DocumentFileRepository,
        comment_repo: CommentRepository,
        notification_service: NotificationService,
    ) -> None:
        self._project_service = project_service
        self._worker_repo = worker_repo
        self._cr_repo = cr_repo
        self._bug_repo = bug_repo
        self._doc_repo = doc_repo
        self._comment_repo = comment_repo
        self._notification_service = notification_service

    # ── prompt generation (former worker_prompt module) ──────────────────────

    async def _fetch_comments(self, entity_type: str, entity_id: uuid.UUID) -> str:
        """Fetch comments with author and timestamp, return formatted section or empty string."""
        comments = await self._comment_repo.find_by_entity(entity_type, entity_id)
        if not comments:
            return ""

        # Batch-load authors to avoid N+1
        user_ids = list({str(c.author_id) for c in comments})
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        users_by_id = {str(u.id): u for u in users}

        lines = ["\n\n---\n\n## Comments\n"]
        for c in comments:
            author_obj = users_by_id.get(str(c.author_id))
            author = author_obj.display_name if author_obj else "Unknown"
            lines.append(f"- **{author}** ({c.created_at:%Y-%m-%d %H:%M}): {c.body}")

        return "\n".join(lines)

    async def generate_prompt(
        self,
        project_id: uuid.UUID,
        entity_type: str | None,
        entity_id: uuid.UUID | None,
        job_type: str = "build",
        branch: str | None = None,
    ) -> str:
        """Generate a full agent prompt for the given job type and entity."""
        # ── build job: project-level, no entity ──────────────────────────────
        if job_type == "build" or (entity_type is None and entity_id is None):
            return (
                "You are running a full SDD build for this project.\n\n"
                "## Workflow\n\n"
                "1. **Pull** — Run `sdd pull` to fetch the latest documentation, "
                "change requests, and bugs from the remote server.\n\n"
                "2. **Build** — Run the `sdd` skill. It handles the full development loop:\n"
                "   - Check for open bugs (`sdd bug open`) and fix them, "
                "then `sdd mark-bug-resolved`\n"
                "   - Check for pending change requests (`sdd cr pending`), apply them "
                "to the docs, then `sdd mark-cr-applied`\n"
                "   - Run `sdd sync` to see which documentation files need to be "
                "implemented in code\n"
                "   - Read the listed docs and implement the required changes inside `code/`\n"
                "   - Run `sdd mark-synced` then **commit immediately** "
                '(`git add -A && git commit -m "sdd sync: ..."`) — mandatory\n\n'
                "3. **Push** — Run `sdd push` to publish the updated code, documentation, "
                "and status transitions back to the remote.\n"
                f"{_REPORT_SECTION}"
            )

        # ── entity-scoped jobs ────────────────────────────────────────────────
        assert entity_type is not None, "entity_type is required for entity-scoped jobs"
        assert entity_id is not None, "entity_id is required for entity-scoped jobs"
        if entity_type == "change_request":
            entity = await self._cr_repo.find_by_id(entity_id)
            if not entity or str(entity.project_id) != str(project_id):
                raise ValueError(f"Change request {entity_id} not found")
            entity_section = (
                f"# Change Request: {entity.title}\n\n"
                f"Status: {entity.status.value}\n\n"
                f"{entity.body}"
            )

        elif entity_type == "bug":
            entity = await self._bug_repo.find_by_id(entity_id)
            if not entity or str(entity.project_id) != str(project_id):
                raise ValueError(f"Bug {entity_id} not found")
            entity_section = (
                f"# Bug: {entity.title}\n\n"
                f"Status: {entity.status.value}\n"
                f"Severity: {entity.severity.value}\n\n"
                f"{entity.body}"
            )

        elif entity_type == "document":
            entity = await self._doc_repo.find_by_id(entity_id)
            if not entity or str(entity.project_id) != str(project_id):
                raise ValueError(f"Document {entity_id} not found")
            entity_section = (
                f"# Document: {entity.title}\n\n"
                f"Path: {entity.path}\n"
                f"Status: {entity.status.value}\n\n"
                f"{entity.content}"
            )

        else:
            raise ValueError(f"Unknown entity_type: {entity_type}")

        # Comments (not available for documents)
        comments_section = ""
        if entity_type in ("change_request", "bug"):
            comments_section = await self._fetch_comments(entity_type, entity_id)

        if job_type != "enrich":
            raise ValueError(f"Unsupported job_type for entity: {job_type}")

        if entity_type == "document":
            prompt = (
                f"sdd pull --docs-only\n\n"
                f"Enrich the following document. Find the local file at `{entity.path}` "  # type: ignore[possibly-undefined]
                f"and rewrite its content with the enriched version — more complete, "
                f"well-structured, and detailed enough to serve as authoritative reference.\n"
                f"Then run `sdd push`.\n"
                f"---\n\n"
                f"{entity_section}"
                f"{_REPORT_SECTION}"
            )
        else:
            if entity_type == "change_request":
                pull_flag = "--crs-only"
                kind_label = "Change Request draft"
            else:  # bug
                pull_flag = "--bugs-only"
                kind_label = "Bug draft"

            prompt = (
                f"sdd pull {pull_flag}\n\n"
                f"Enrich the following {kind_label}. Find the corresponding local file "
                f"and rewrite its content with the enriched version — add technical details, "
                f"acceptance criteria, edge cases, and implementation hints.\n"
                f"Then run `sdd mark-drafts-enriched <file>` on that specific file only, "
                f"then run `sdd push`.\n"
                f"---\n\n"
                f"{entity_section}"
                f"{comments_section}"
                f"{_REPORT_SECTION}"
            )

        return prompt

    # ── entity validation / title helpers ────────────────────────────────────

    async def validate_entity(
        self,
        project_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        job_type: JobType,
    ) -> str:
        """Validate entity exists and has correct status for the job type. Returns entity title."""
        if entity_type == "change_request":
            entity = await self._cr_repo.find_by_id(entity_id)
            if entity is None or entity.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found"
                )
            if entity.status != CRStatus.draft:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CR must be in 'draft' status to enrich",
                )
            return entity.title

        elif entity_type == "bug":
            entity = await self._bug_repo.find_by_id(entity_id)
            if entity is None or entity.project_id != project_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")
            if entity.status != BugStatus.draft:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bug must be in 'draft' status to enrich",
                )
            return entity.title

        elif entity_type == "document":
            entity = await self._doc_repo.find_by_id(entity_id)
            if entity is None or entity.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )
            if entity.status == DocStatus.deleted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot enrich a deleted document",
                )
            return entity.title

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity_type"
            )

    async def get_entity_title(
        self, entity_type: str | None, entity_id: uuid.UUID | None
    ) -> str | None:
        if entity_type is None or entity_id is None:
            return None
        if entity_type == "change_request":
            cr = await self._cr_repo.find_by_id(entity_id)
            return cr.title if cr else None
        elif entity_type == "bug":
            bug = await self._bug_repo.find_by_id(entity_id)
            return bug.title if bug else None
        elif entity_type == "document":
            doc = await self._doc_repo.find_by_id(entity_id)
            return doc.title if doc else None
        return None

    # ── Web endpoints (workers & jobs) ────────────────────────────────────────

    async def list_workers(self, tenant_id: uuid.UUID, project_id: uuid.UUID) -> list[Worker]:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        workers = await self._worker_repo.find_by_project(project_id)
        # Sort by registered_at desc
        return sorted(workers, key=lambda w: w.registered_at, reverse=True)

    async def preview_job(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, body: WorkerJobPreviewRequest
    ) -> str:
        """Generate the prompt for a job without creating it."""
        await self._project_service.get_project_or_404(tenant_id, project_id)

        if body.job_type in (JobType.build, JobType.custom):
            # Project-level jobs — no entity required
            pass
        else:
            if body.entity_type is None or body.entity_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="entity_type and entity_id are required for enrich jobs",
                )
            await self.validate_entity(project_id, body.entity_type, body.entity_id, body.job_type)

        if body.job_type == JobType.custom:
            return ""

        return await self.generate_prompt(
            project_id, body.entity_type, body.entity_id, job_type=body.job_type.value
        )

    async def create_job(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        body: WorkerJobCreate,
        actor_user_id: uuid.UUID,
    ) -> tuple[WorkerJob, str | None]:
        """Create a queued worker job; returns (job, entity_title)."""
        await self._project_service.get_project_or_404(tenant_id, project_id)

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
            entity_title = await self.validate_entity(
                project_id, body.entity_type, body.entity_id, body.job_type
            )

        # Resolve worker and its branch
        target_worker = None
        if body.worker_id:
            target_worker = await self._worker_repo.find_by_id(body.worker_id)
            if target_worker is None or target_worker.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found"
                )
            worker_branch = target_worker.branch

        # Determine agent
        agent = body.agent
        if not agent:
            if target_worker:
                agent = target_worker.agent
            else:
                online_worker = await self._worker_repo.find_online_worker(project_id)
                agent = online_worker.agent if online_worker else "claude"

        # Generate or use override prompt
        if body.prompt:
            prompt = body.prompt
        else:
            prompt = await self.generate_prompt(
                project_id,
                body.entity_type,
                body.entity_id,
                job_type=body.job_type.value,
                branch=worker_branch,
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
            created_by=actor_user_id,
        )
        await job.insert()

        return job, entity_title

    async def list_jobs(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        page: int,
        page_size: int,
        status_filter: JobStatus | None = None,
    ) -> tuple[list[tuple[WorkerJob, str | None, str | None]], int]:
        """Paginated jobs with (worker_name, entity_title) resolved per job (no N+1)."""
        await self._project_service.get_project_or_404(tenant_id, project_id)

        jobs, total = await self._worker_repo.find_jobs_by_project(
            project_id, status=status_filter, page=page, page_size=page_size
        )

        # Batch worker names
        worker_ids = list({j.worker_id for j in jobs if j.worker_id})
        workers_by_id = await self._worker_repo.find_by_ids(worker_ids) if worker_ids else {}

        # Batch entity titles by type
        cr_ids = [j.entity_id for j in jobs if j.entity_type == "change_request" and j.entity_id]
        bug_ids = [j.entity_id for j in jobs if j.entity_type == "bug" and j.entity_id]
        doc_ids = [j.entity_id for j in jobs if j.entity_type == "document" and j.entity_id]

        cr_titles = (
            {cr.id: cr.title for cr in (await self._cr_repo.find_by_ids_batch(cr_ids)).values()}
            if cr_ids
            else {}
        )
        bug_titles = (
            {b.id: b.title for b in (await self._bug_repo.find_by_ids_batch(bug_ids)).values()}
            if bug_ids
            else {}
        )
        doc_titles = (
            {d.id: d.title for d in (await self._doc_repo.find_by_ids_batch(doc_ids)).values()}
            if doc_ids
            else {}
        )

        items: list[tuple[WorkerJob, str | None, str | None]] = []
        for job in jobs:
            worker_name = (
                workers_by_id[job.worker_id].name
                if job.worker_id and job.worker_id in workers_by_id
                else None
            )
            entity_title = None
            if job.entity_type == "change_request" and job.entity_id:
                entity_title = cr_titles.get(job.entity_id)
            elif job.entity_type == "bug" and job.entity_id:
                entity_title = bug_titles.get(job.entity_id)
            elif job.entity_type == "document" and job.entity_id:
                entity_title = doc_titles.get(job.entity_id)
            items.append((job, worker_name, entity_title))

        return items, total

    async def get_job_with_detail(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, job_id: uuid.UUID
    ) -> tuple[WorkerJob, list[WorkerJobMessage], str | None, str | None]:
        """Returns (job, messages, worker_name, entity_title)."""
        await self._project_service.get_project_or_404(tenant_id, project_id)

        job = await self._worker_repo.find_job_by_id(job_id)
        if job is None or job.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        messages = await self._worker_repo.find_messages(job_id)

        worker_name = None
        if job.worker_id:
            w = await self._worker_repo.find_by_id(job.worker_id)
            worker_name = w.name if w else None

        entity_title = await self.get_entity_title(job.entity_type, job.entity_id)
        return job, messages, worker_name, entity_title

    async def get_job_or_404(self, job_id: uuid.UUID, project_id: uuid.UUID) -> WorkerJob:
        job = await self._worker_repo.find_job_by_id(job_id)
        if job is None or job.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    async def stream_events(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, job_id: uuid.UUID
    ) -> AsyncGenerator[str]:
        """SSE generator streaming job messages in real-time.

        Self-contained: polls the database every 0.5s until the job reaches a
        terminal status. Yields SSE-formatted strings.
        """
        await self._project_service.get_project_or_404(tenant_id, project_id)

        job = await self._worker_repo.find_job_by_id(job_id)
        if job is None or job.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        last_sequence = 0
        while True:
            messages = await self._worker_repo.find_messages(job_id, after_sequence=last_sequence)

            for msg in messages:
                data = json.dumps(
                    {
                        "id": str(msg.id),
                        "job_id": str(msg.job_id),
                        "kind": msg.kind.value,
                        "content": msg.content,
                        "sequence": msg.sequence,
                        "created_at": msg.created_at.isoformat(),
                    }
                )
                yield f"data: {data}\n\n"
                last_sequence = msg.sequence

            current_job = await self._worker_repo.find_job_by_id(job_id)
            if current_job and current_job.status in (
                JobStatus.completed,
                JobStatus.failed,
                JobStatus.cancelled,
            ):
                done_data = json.dumps(
                    {
                        "type": "done",
                        "status": current_job.status.value,
                        "exit_code": current_job.exit_code,
                    }
                )
                yield f"event: done\ndata: {done_data}\n\n"
                break

            await asyncio.sleep(0.5)

    async def answer_question(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, job_id: uuid.UUID, content: str
    ) -> WorkerJobMessage:
        """User answers a question from the agent."""
        await self._project_service.get_project_or_404(tenant_id, project_id)

        job = await self._worker_repo.find_job_by_id(job_id)
        if job is None or job.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        messages = await self._worker_repo.find_messages(job_id)
        max_seq = messages[-1].sequence if messages else 0

        msg = WorkerJobMessage(
            job_id=job_id,
            kind=MessageKind.answer,
            content=content,
            sequence=max_seq + 1,
        )
        await self._worker_repo.create_message(msg)

        return msg

    async def cancel_job(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, job_id: uuid.UUID
    ) -> None:
        """Cancel a queued or running job."""
        await self._project_service.get_project_or_404(tenant_id, project_id)

        job = await self._worker_repo.find_job_by_id(job_id)
        if job is None or job.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        if job.status not in (JobStatus.queued, JobStatus.assigned, JobStatus.running):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job in status '{job.status.value}'",
            )

        await job.set(
            {
                WorkerJob.status: JobStatus.cancelled,
                WorkerJob.completed_at: datetime.now(UTC),
            }
        )

    # ── CLI daemon flows (worker side) ────────────────────────────────────────

    async def register_worker(self, project_id: uuid.UUID, body: WorkerRegisterRequest) -> Worker:
        """Register or reconnect a worker. Upserts by (project_id, name)."""
        return await self._worker_repo.register_or_update(
            project_id=project_id,
            name=body.name,
            agent=body.agent,
            branch=body.branch,
            metadata=body.metadata or {},
        )

    async def get_worker_or_404(self, worker_id: uuid.UUID, project_id: uuid.UUID) -> Worker:
        worker = await self._worker_repo.find_by_id(worker_id)
        if worker is None or str(worker.project_id) != str(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
        return worker

    async def worker_heartbeat(
        self, worker_id: uuid.UUID, project_id: uuid.UUID, status_value: Any
    ) -> None:
        """Update worker heartbeat and status."""
        worker = await self.get_worker_or_404(worker_id, project_id)
        await worker.set(
            {
                Worker.status: status_value,
                Worker.last_heartbeat_at: utcnow(),
            }
        )

    async def poll_for_job(
        self,
        worker_id: uuid.UUID,
        project_id: uuid.UUID,
        poll_duration: int = 30,
        poll_interval: int = 1,
    ) -> tuple[WorkerJob | None, Worker]:
        """Long-poll loop for a queued job (up to `poll_duration` seconds)."""
        worker = await self.get_worker_or_404(worker_id, project_id)

        for _ in range(poll_duration):
            job = await self._worker_repo.assign_job(project_id, worker_id)
            if job is not None:
                await worker.set(
                    {
                        Worker.status: WorkerStatus.busy,
                        Worker.last_heartbeat_at: utcnow(),
                    }
                )
                return job, worker
            await asyncio.sleep(poll_interval)

        return None, worker

    async def job_started(self, job_id: uuid.UUID, project_id: uuid.UUID) -> None:
        """Worker notifies that the agent process has started."""
        job = await self.get_job_or_404(job_id, project_id)
        await job.set(
            {
                WorkerJob.status: JobStatus.running,
                WorkerJob.started_at: utcnow(),
            }
        )

    async def job_output(self, job_id: uuid.UUID, lines: list[str]) -> int:
        """Worker posts batched output lines. Returns the number stored."""
        existing_messages = await self._worker_repo.find_messages(job_id)
        max_seq = existing_messages[-1].sequence if existing_messages else 0

        for i, line in enumerate(lines):
            msg = WorkerJobMessage(
                job_id=job_id,
                kind=MessageKind.output,
                content=line,
                sequence=max_seq + i + 1,
            )
            await self._worker_repo.create_message(msg)

        return len(lines)

    async def job_question(
        self,
        job_id: uuid.UUID,
        content: str,
        project_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> WorkerJobMessage:
        """Worker posts a question from the agent; notifies the job creator."""
        existing_messages = await self._worker_repo.find_messages(job_id)
        max_seq = existing_messages[-1].sequence if existing_messages else 0

        msg = WorkerJobMessage(
            job_id=job_id,
            kind=MessageKind.question,
            content=content,
            sequence=max_seq + 1,
        )
        await self._worker_repo.create_message(msg)

        # Notify the job creator
        job = await self._worker_repo.find_job_by_id(job_id)
        if job and str(job.project_id) == str(project_id):
            await self._notification_service.create_notification(
                user_id=job.created_by,
                tenant_id=tenant_id,
                event_type="worker_question",
                entity_type="worker_job",
                entity_id=job_id,
                title=f"Worker needs your attention on job #{str(job_id)[:8]}",
            )

        return msg

    async def job_answers(
        self, job_id: uuid.UUID, after_sequence: int = 0
    ) -> list[WorkerJobMessage]:
        """Worker reads answers from the user (new answers since after_sequence)."""
        return await self._worker_repo.find_messages(
            job_id, after_sequence=after_sequence, kind=MessageKind.answer
        )

    async def job_completed(
        self,
        job_id: uuid.UUID,
        exit_code: int,
        changed_files: list[ChangedFile] | None,
        project_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> tuple[JobStatus, int]:
        """Worker reports job completion. Auto-transitions the entity on success."""
        job = await self.get_job_or_404(job_id, project_id)

        now = utcnow()
        new_status = JobStatus.completed if exit_code == 0 else JobStatus.failed
        updates: dict[Any, Any] = {
            WorkerJob.exit_code: exit_code,
            WorkerJob.completed_at: now,
            WorkerJob.status: new_status,
        }
        if changed_files:
            updates[WorkerJob.changed_files] = [f.model_dump() for f in changed_files]
        await job.set(updates)

        # Set worker back to online
        if job.worker_id:
            worker = await self._worker_repo.find_by_id(job.worker_id)
            if worker:
                await worker.set({Worker.status: WorkerStatus.online})

        # Auto-transition entity on success
        if exit_code == 0:
            if job.entity_type == "change_request" and job.entity_id:
                cr = await self._cr_repo.find_by_id(job.entity_id)
                if cr and cr.status == CRStatus.draft:
                    await cr.set({ChangeRequest.status: CRStatus.pending})

            elif job.entity_type == "document" and job.entity_id:
                doc = await self._doc_repo.find_by_id(job.entity_id)
                if doc and doc.status == DocStatus.draft:
                    await doc.set({DocumentFile.status: DocStatus.new})

        # Send notification to job creator
        event_type = "worker_job_completed" if exit_code == 0 else "worker_job_failed"
        status_label = "completed" if exit_code == 0 else "failed"
        await self._notification_service.create_notification(
            user_id=job.created_by,
            tenant_id=tenant_id,
            event_type=event_type,
            entity_type="worker_job",
            entity_id=job_id,
            title=f"Worker job #{str(job_id)[:8]} {status_label}",
        )

        return new_status, exit_code
