from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from beanie import SortDirection

from app.models.base import utcnow
from app.models.worker import Worker, WorkerStatus
from app.models.worker_job import JobStatus, WorkerJob
from app.models.worker_job_message import MessageKind, WorkerJobMessage
from app.utils.bson import uuid_to_bin
from app.utils.mongo import raw_collection


class WorkerRepository:
    async def find_by_id(self, id: UUID) -> Worker | None:
        return await Worker.get(id)

    async def find_by_ids(self, ids: list[UUID]) -> dict[UUID, Worker]:
        id_bins = [uuid_to_bin(i) for i in ids]
        items = await Worker.find({"_id": {"$in": id_bins}}).to_list()
        return {w.id: w for w in items}

    async def find_online_worker(self, project_id: UUID) -> Worker | None:
        return await Worker.find_one({"projectId": project_id, "status": WorkerStatus.online.value})

    async def find_by_project(self, project_id: UUID) -> list[Worker]:
        return await Worker.find({"projectId": project_id}).to_list()

    async def register_or_update(
        self,
        project_id: UUID,
        name: str,
        agent: str,
        branch: str | None,
        metadata: dict[str, Any],
    ) -> Worker:
        col = raw_collection(Worker)
        now = utcnow()
        pid_bin = uuid_to_bin(project_id)
        new_id_bin = uuid_to_bin(uuid4())
        await col.find_one_and_update(
            {"projectId": pid_bin, "name": name},
            {
                "$set": {
                    "agent": agent,
                    "branch": branch,
                    "metadata": metadata,
                    "status": WorkerStatus.online.value,
                    "lastHeartbeatAt": now,
                    "updatedAt": now,
                },
                "$setOnInsert": {
                    "_id": new_id_bin,
                    "projectId": pid_bin,
                    "name": name,
                    "registeredAt": now,
                    "createdAt": now,
                },
            },
            upsert=True,
            return_document=True,
        )
        worker = await Worker.find_one({"projectId": project_id, "name": name})
        assert worker is not None, "upsert completed but worker not found"
        return worker

    async def update_heartbeat(self, worker_id: UUID) -> None:
        col = raw_collection(Worker)
        now = utcnow()
        await col.update_one(
            {"_id": uuid_to_bin(worker_id)},
            {"$set": {"lastHeartbeatAt": now, "updatedAt": now}},
        )

    async def mark_stale_workers_offline(self, threshold_seconds: int = 60) -> int:
        col = raw_collection(Worker)
        cutoff = utcnow() - timedelta(seconds=threshold_seconds)
        result = await col.update_many(
            {
                "status": {"$ne": WorkerStatus.offline.value},
                "lastHeartbeatAt": {"$lt": cutoff},
            },
            {"$set": {"status": WorkerStatus.offline.value, "updatedAt": utcnow()}},
        )
        return result.modified_count

    async def fail_orphaned_jobs(self, offline_threshold_seconds: int = 300) -> int:
        col = raw_collection(WorkerJob)
        cutoff = utcnow() - timedelta(seconds=offline_threshold_seconds)
        offline_workers = await Worker.find(
            {"status": WorkerStatus.offline.value, "lastHeartbeatAt": {"$lt": cutoff}}
        ).to_list()
        if not offline_workers:
            return 0
        worker_id_bins = [uuid_to_bin(w.id) for w in offline_workers]
        now = utcnow()
        result = await col.update_many(
            {
                "workerId": {"$in": worker_id_bins},
                "status": {"$in": [JobStatus.assigned.value, JobStatus.running.value]},
            },
            {"$set": {"status": JobStatus.failed.value, "updatedAt": now, "completedAt": now}},
        )
        return result.modified_count

    async def find_job_by_id(self, id: UUID) -> WorkerJob | None:
        return await WorkerJob.get(id)

    async def find_jobs_by_project(
        self,
        project_id: UUID,
        status: JobStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WorkerJob], int]:
        query: dict[str, Any] = {"projectId": project_id}
        if status is not None:
            query["status"] = status.value
        skip = (page - 1) * page_size
        total = await WorkerJob.find(query).count()
        items = (
            await WorkerJob.find(query)
            .sort([("createdAt", SortDirection.DESCENDING)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def assign_job(self, project_id: UUID, worker_id: UUID) -> WorkerJob | None:
        col = raw_collection(WorkerJob)
        now = utcnow()
        pid_bin = uuid_to_bin(project_id)
        wid_bin = uuid_to_bin(worker_id)
        result = await col.find_one_and_update(
            {"projectId": pid_bin, "status": JobStatus.queued.value},
            {
                "$set": {
                    "status": JobStatus.assigned.value,
                    "workerId": wid_bin,
                    "updatedAt": now,
                }
            },
            sort=[("createdAt", 1)],
            return_document=True,
        )
        if result is None:
            return None
        return await WorkerJob.get(result["_id"])

    async def save_job(self, job: WorkerJob) -> WorkerJob:
        await job.save()
        return job

    async def find_messages(
        self,
        job_id: UUID,
        after_sequence: int = 0,
        kind: MessageKind | None = None,
    ) -> list[WorkerJobMessage]:
        query: dict[str, Any] = {"jobId": job_id, "sequence": {"$gt": after_sequence}}
        if kind is not None:
            query["kind"] = kind.value if hasattr(kind, "value") else kind
        return (
            await WorkerJobMessage.find(query)
            .sort([("sequence", SortDirection.ASCENDING)])
            .to_list()
        )

    async def create_message(self, msg: WorkerJobMessage) -> WorkerJobMessage:
        await msg.insert()
        return msg

    async def delete_by_project(self, project_id: UUID) -> dict[str, Any]:
        job_ids = [
            uuid_to_bin(j.id) for j in await WorkerJob.find({"projectId": project_id}).to_list()
        ]

        msg_count = 0
        if job_ids:
            msg_result = await WorkerJobMessage.find({"jobId": {"$in": job_ids}}).delete()
            msg_count = msg_result.deleted_count if msg_result else 0

        job_result = await WorkerJob.find({"projectId": project_id}).delete()
        job_count = job_result.deleted_count if job_result else 0

        worker_result = await Worker.find({"projectId": project_id}).delete()
        worker_count = worker_result.deleted_count if worker_result else 0

        return {
            "workers": worker_count,
            "jobs": job_count,
            "messages": msg_count,
        }
