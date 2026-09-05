"""Tenant dashboard aggregate service."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast

from beanie import Document
from fastapi import HTTPException, status

from app.models.bug import Bug, BugSeverity, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.comment import Comment, EntityType
from app.models.document_file import DocStatus, DocumentFile
from app.models.worker import Worker
from app.repositories import AuditRepository, ProjectRepository, TenantRepository
from app.schemas.tenant_dashboard import (
    TenantDashboardKpis,
    TenantDashboardProject,
    TenantDashboardProjectStats,
    TenantDashboardResponse,
    TenantDashboardTenant,
    TenantDashboardWindow,
)
from app.utils.bson import bin_to_uuid, uuid_to_bin
from app.utils.mongo import raw_collection

DashboardWindowPreset = Literal["last_7_days", "last_30_days", "last_90_days"]

_WINDOW_DAYS: dict[DashboardWindowPreset, int] = {
    "last_7_days": 7,
    "last_30_days": 30,
    "last_90_days": 90,
}


class TenantDashboardService:
    def __init__(
        self,
        tenant_repo: TenantRepository,
        project_repo: ProjectRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._project_repo = project_repo
        self._audit_repo = audit_repo

    async def get_dashboard(
        self,
        tenant_id: uuid.UUID,
        window_preset: DashboardWindowPreset = "last_30_days",
        include_archived: bool = False,
    ) -> TenantDashboardResponse:
        tenant = await self._tenant_repo.find_by_id(tenant_id)
        if tenant is None:
            # The auth dependency normally guarantees membership to an existing
            # tenant, but keep a safe fallback for tests/direct calls.
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        now = datetime.now(UTC)
        from_dt = now - timedelta(days=_WINDOW_DAYS[window_preset])

        active_projects = await self._project_repo.find_by_tenant(tenant_id, include_archived=False)
        portfolio_projects = await self._project_repo.find_by_tenant(
            tenant_id, include_archived=include_archived
        )
        archived_projects = [
            project for project in portfolio_projects if project.archived_at is not None
        ]
        if not include_archived:
            all_projects = await self._project_repo.find_by_tenant(tenant_id, include_archived=True)
            archived_count = sum(1 for project in all_projects if project.archived_at is not None)
        else:
            archived_count = len(archived_projects)

        active_project_ids = [project.id for project in active_projects]
        portfolio_project_ids = [project.id for project in portfolio_projects]

        active_stats = await self._aggregate_project_stats(active_project_ids, from_dt, now)
        portfolio_stats = await self._aggregate_project_stats(portfolio_project_ids, from_dt, now)

        _activity_entries, activity_total = await self._audit_repo.find_by_tenant_filtered(
            tenant_id=tenant_id,
            from_dt=from_dt,
            to_dt=now,
            page=1,
            page_size=1,
        )

        kpis = self._build_kpis(
            active_projects=len(active_projects),
            archived_projects=archived_count,
            project_stats=active_stats,
            activity_events_in_window=activity_total,
        )

        dashboard_projects = [
            TenantDashboardProject(
                id=project.id,
                name=project.name,
                slug=project.slug,
                description=project.description,
                archived_at=project.archived_at,
                stats=portfolio_stats.get(project.id, TenantDashboardProjectStats()),
            )
            for project in portfolio_projects
        ]

        return TenantDashboardResponse(
            tenant=TenantDashboardTenant(id=tenant.id, name=tenant.name, slug=tenant.slug),
            window=TenantDashboardWindow.model_validate(
                {"preset": window_preset, "from": from_dt, "to": now}
            ),
            kpis=kpis,
            projects=dashboard_projects,
        )

    async def _aggregate_project_stats(
        self, project_ids: list[uuid.UUID], from_dt: datetime, to_dt: datetime
    ) -> dict[uuid.UUID, TenantDashboardProjectStats]:
        stats = {project_id: TenantDashboardProjectStats() for project_id in project_ids}
        if not project_ids:
            return stats

        await self._apply_doc_stats(stats, project_ids)
        await self._apply_bug_stats(stats, project_ids)
        await self._apply_cr_stats(stats, project_ids)
        await self._apply_worker_stats(stats, project_ids, to_dt)
        await self._apply_comment_stats(stats, project_ids, from_dt, to_dt)
        await self._apply_last_activity(stats, project_ids)
        return stats

    async def _apply_doc_stats(
        self, stats: dict[uuid.UUID, TenantDashboardProjectStats], project_ids: list[uuid.UUID]
    ) -> None:
        pipeline: list[dict[str, Any]] = [
            {"$match": {"projectId": {"$in": self._project_id_bins(project_ids)}}},
            {
                "$group": {
                    "_id": "$projectId",
                    "documents_total": {
                        "$sum": {"$cond": [{"$ne": ["$status", DocStatus.deleted.value]}, 1, 0]}
                    },
                    "documents_synced": {
                        "$sum": {"$cond": [{"$eq": ["$status", DocStatus.synced.value]}, 1, 0]}
                    },
                    "documents_pending": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$in": [
                                        "$status",
                                        [
                                            DocStatus.new.value,
                                            DocStatus.changed.value,
                                            DocStatus.deleted.value,
                                        ],
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]
        async for row in await raw_collection(DocumentFile).aggregate(pipeline):
            project_id = self._row_project_id(row)
            if project_id in stats:
                stats[project_id].documents_total = int(row.get("documents_total", 0))
                stats[project_id].documents_synced = int(row.get("documents_synced", 0))
                stats[project_id].documents_pending = int(row.get("documents_pending", 0))

    async def _apply_bug_stats(
        self, stats: dict[uuid.UUID, TenantDashboardProjectStats], project_ids: list[uuid.UUID]
    ) -> None:
        open_statuses = [BugStatus.open.value, BugStatus.in_progress.value]
        pipeline: list[dict[str, Any]] = [
            {"$match": {"projectId": {"$in": self._project_id_bins(project_ids)}}},
            {
                "$group": {
                    "_id": "$projectId",
                    "open_bugs": {"$sum": {"$cond": [{"$in": ["$status", open_statuses]}, 1, 0]}},
                    "critical_bugs": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$in": ["$status", open_statuses]},
                                        {"$eq": ["$severity", BugSeverity.critical.value]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "major_bugs": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$in": ["$status", open_statuses]},
                                        {"$eq": ["$severity", BugSeverity.major.value]},
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]
        async for row in await raw_collection(Bug).aggregate(pipeline):
            project_id = self._row_project_id(row)
            if project_id in stats:
                stats[project_id].open_bugs = int(row.get("open_bugs", 0))
                stats[project_id].critical_bugs = int(row.get("critical_bugs", 0))
                stats[project_id].major_bugs = int(row.get("major_bugs", 0))

    async def _apply_cr_stats(
        self, stats: dict[uuid.UUID, TenantDashboardProjectStats], project_ids: list[uuid.UUID]
    ) -> None:
        active_statuses = [CRStatus.draft.value, CRStatus.pending.value, CRStatus.approved.value]
        review_statuses = [CRStatus.pending.value, CRStatus.approved.value]
        pipeline: list[dict[str, Any]] = [
            {"$match": {"projectId": {"$in": self._project_id_bins(project_ids)}}},
            {
                "$group": {
                    "_id": "$projectId",
                    "active_crs": {
                        "$sum": {"$cond": [{"$in": ["$status", active_statuses]}, 1, 0]}
                    },
                    "review_queue_crs": {
                        "$sum": {"$cond": [{"$in": ["$status", review_statuses]}, 1, 0]}
                    },
                }
            },
        ]
        async for row in await raw_collection(ChangeRequest).aggregate(pipeline):
            project_id = self._row_project_id(row)
            if project_id in stats:
                stats[project_id].active_crs = int(row.get("active_crs", 0))
                stats[project_id].review_queue_crs = int(row.get("review_queue_crs", 0))

    async def _apply_worker_stats(
        self,
        stats: dict[uuid.UUID, TenantDashboardProjectStats],
        project_ids: list[uuid.UUID],
        now: datetime,
    ) -> None:
        heartbeat_cutoff = now - timedelta(seconds=60)
        pipeline: list[dict[str, Any]] = [
            {"$match": {"projectId": {"$in": self._project_id_bins(project_ids)}}},
            {
                "$group": {
                    "_id": "$projectId",
                    "workers_total": {"$sum": 1},
                    "workers_online": {
                        "$sum": {"$cond": [{"$gte": ["$lastHeartbeatAt", heartbeat_cutoff]}, 1, 0]}
                    },
                }
            },
        ]
        async for row in await raw_collection(Worker).aggregate(pipeline):
            project_id = self._row_project_id(row)
            if project_id in stats:
                stats[project_id].workers_total = int(row.get("workers_total", 0))
                stats[project_id].workers_online = int(row.get("workers_online", 0))

    async def _apply_comment_stats(
        self,
        stats: dict[uuid.UUID, TenantDashboardProjectStats],
        project_ids: list[uuid.UUID],
        from_dt: datetime,
        to_dt: datetime,
    ) -> None:
        for entity_type, collection_name in (
            (EntityType.change_request.value, "change_requests"),
            (EntityType.bug.value, "bugs"),
        ):
            pipeline: list[dict[str, Any]] = [
                {
                    "$match": {
                        "entityType": entity_type,
                        "createdAt": {"$gte": from_dt, "$lte": to_dt},
                    }
                },
                {
                    "$lookup": {
                        "from": collection_name,
                        "localField": "entityId",
                        "foreignField": "_id",
                        "as": "entity",
                    }
                },
                {"$unwind": "$entity"},
                {"$match": {"entity.projectId": {"$in": self._project_id_bins(project_ids)}}},
                {
                    "$group": {
                        "_id": "$entity.projectId",
                        "comments": {"$sum": 1},
                        "authors": {"$addToSet": "$authorId"},
                    }
                },
            ]
            async for row in await raw_collection(Comment).aggregate(pipeline):
                project_id = self._row_project_id(row)
                if project_id in stats:
                    authors = {author for author in row.get("authors", []) if author is not None}
                    stats[project_id].comments_in_window += int(row.get("comments", 0))
                    stats[project_id].distinct_commenters_in_window += len(authors)

    async def _apply_last_activity(
        self, stats: dict[uuid.UUID, TenantDashboardProjectStats], project_ids: list[uuid.UUID]
    ) -> None:
        # Direct project-linked activity is not denormalized on all audit events,
        # so last activity is conservatively based on project document updates and
        # per-domain aggregate updates surfaced by each collection.
        collections: list[type[Document]] = [DocumentFile, ChangeRequest, Bug, Worker]
        for model in collections:
            pipeline: list[dict[str, Any]] = [
                {"$match": {"projectId": {"$in": self._project_id_bins(project_ids)}}},
                {"$group": {"_id": "$projectId", "last_activity_at": {"$max": "$updatedAt"}}},
            ]
            async for row in await raw_collection(model).aggregate(pipeline):
                project_id = self._row_project_id(row)
                if project_id in stats:
                    current = stats[project_id].last_activity_at
                    candidate = cast(datetime | None, row.get("last_activity_at"))
                    if candidate is not None and (current is None or candidate > current):
                        stats[project_id].last_activity_at = candidate

    def _build_kpis(
        self,
        active_projects: int,
        archived_projects: int,
        project_stats: dict[uuid.UUID, TenantDashboardProjectStats],
        activity_events_in_window: int,
    ) -> TenantDashboardKpis:
        documents_total = sum(stat.documents_total for stat in project_stats.values())
        documents_synced = sum(stat.documents_synced for stat in project_stats.values())
        docs_sync_percentage = (
            round((documents_synced / documents_total) * 100) if documents_total > 0 else 0
        )
        return TenantDashboardKpis(
            active_projects=active_projects,
            archived_projects=archived_projects,
            documents_total=documents_total,
            documents_synced=documents_synced,
            documents_pending=sum(stat.documents_pending for stat in project_stats.values()),
            docs_sync_percentage=docs_sync_percentage,
            open_bugs=sum(stat.open_bugs for stat in project_stats.values()),
            critical_bugs=sum(stat.critical_bugs for stat in project_stats.values()),
            major_bugs=sum(stat.major_bugs for stat in project_stats.values()),
            active_crs=sum(stat.active_crs for stat in project_stats.values()),
            review_queue_crs=sum(stat.review_queue_crs for stat in project_stats.values()),
            comments_in_window=sum(stat.comments_in_window for stat in project_stats.values()),
            distinct_commenters_in_window=sum(
                stat.distinct_commenters_in_window for stat in project_stats.values()
            ),
            activity_events_in_window=activity_events_in_window,
            workers_online=sum(stat.workers_online for stat in project_stats.values()),
            workers_total=sum(stat.workers_total for stat in project_stats.values()),
        )

    @staticmethod
    def _project_id_bins(project_ids: list[uuid.UUID]) -> list[Any]:
        return [uuid_to_bin(project_id) for project_id in project_ids]

    @staticmethod
    def _row_project_id(row: dict[str, Any]) -> uuid.UUID:
        project_id = bin_to_uuid(row["_id"])
        if project_id is None:
            raise ValueError("aggregate row does not contain a UUID project id")
        return project_id
