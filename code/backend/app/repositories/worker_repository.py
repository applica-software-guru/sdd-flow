from typing import Optional
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.utils.bson import uuid_to_bin, bin_to_uuid

from app.models.worker import Worker, WorkerStatus
from app.models.worker_job import WorkerJob, JobStatus
from app.models.worker_job_message import WorkerJobMessage
from app.models.base import utcnow




class WorkerRepository:
    async def find_by_id(self, id: UUID) -> Optional[Worker]:
        return await Worker.get(id)

    async def find_by_project(self, project_id: UUID) -> list[Worker]:
        return await Worker.find({"projectId": project_id}).to_list()

    async def register_or_update(
        self,
        project_id: UUID,
        name: str,
        agent: str,
        branch: Optional[str],
        metadata: dict,
    ) -> Worker:
        col = Worker.get_pymongo_collection()
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
        return await Worker.find_one({"projectId": project_id, "name": name})

    async def update_heartbeat(self, worker_id: UUID) -> None:
        col = Worker.get_pymongo_collection()
        now = utcnow()
        await col.update_one(
            {"_id": uuid_to_bin(worker_id)},
            {"$set": {"lastHeartbeatAt": now, "updatedAt": now}},
        )

    async def mark_stale_workers_offline(self, threshold_seconds: int = 60) -> int:
        col = Worker.get_pymongo_collection()
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
        col = WorkerJob.get_pymongo_collection()
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

    async def find_job_by_id(self, id: UUID) -> Optional[WorkerJob]:
        return await WorkerJob.get(id)

    async def find_jobs_by_project(
        self,
        project_id: UUID,
        status: Optional[JobStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WorkerJob], int]:
        query: dict = {"projectId": project_id}
        if status is not None:
            query["status"] = status.value
        skip = (page - 1) * page_size
        total = await WorkerJob.find(query).count()
        items = (
            await WorkerJob.find(query)
            .sort([("createdAt", -1)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def assign_job(
        self, project_id: UUID, worker_id: UUID
    ) -> Optional[WorkerJob]:
        col = WorkerJob.get_pymongo_collection()
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
        self, job_id: UUID, after_sequence: int = 0
    ) -> list[WorkerJobMessage]:
        return (
            await WorkerJobMessage.find(
                {"jobId": job_id, "sequence": {"$gt": after_sequence}}
            )
            .sort([("sequence", 1)])
            .to_list()
        )

    async def create_message(self, msg: WorkerJobMessage) -> WorkerJobMessage:
        await msg.insert()
        return msg

    async def delete_by_project(self, project_id: UUID) -> dict:
        workers = await Worker.find({"projectId": project_id}).to_list()
        job_ids = [uuid_to_bin(j.id) for j in await WorkerJob.find({"projectId": project_id}).to_list()]

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
