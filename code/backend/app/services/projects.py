"""Project domain service."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.models.project import Project
from app.repositories import ProjectRepository
from app.schemas.projects import (
    ProjectCreate,
    ProjectResetResponse,
    ProjectResponse,
    ProjectStats,
    ProjectUpdate,
)
from app.services.audit import AuditService
from app.services.project_reset import ProjectResetService


def _stats_for(stats_dict: dict[uuid.UUID, dict[str, int]], project_id: uuid.UUID) -> ProjectStats:
    stats_data = stats_dict.get(
        project_id, {"doc_count": 0, "open_cr_count": 0, "open_bug_count": 0}
    )
    return ProjectStats(
        document_count=stats_data["doc_count"],
        open_cr_count=stats_data["open_cr_count"],
        open_bug_count=stats_data["open_bug_count"],
    )


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        audit_service: AuditService,
        reset_service: ProjectResetService,
    ) -> None:
        self._project_repo = project_repo
        self._audit_service = audit_service
        self._reset_service = reset_service

    async def get_project_or_404(self, tenant_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        """Project scoped to the tenant, or 404 ("Project not found")."""
        project = await self._project_repo.find_by_id(project_id)
        if project is None or project.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    async def _response_with_stats(self, project: Project) -> ProjectResponse:
        stats_dict = await self._project_repo.get_stats_batch([project.id])
        resp = ProjectResponse.model_validate(project)
        resp.stats = _stats_for(stats_dict, project.id)
        return resp

    async def create_project(
        self, tenant_id: uuid.UUID, body: ProjectCreate, actor_user_id: uuid.UUID
    ) -> ProjectResponse:
        existing = await self._project_repo.find_by_slug(tenant_id, body.slug)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Project slug already exists in this tenant",
            )

        project = Project(
            tenant_id=tenant_id, name=body.name, slug=body.slug, description=body.description
        )
        await self._project_repo.save(project)

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "project.created",
            "project",
            project.id,
            entity_label=project.name,
            summary="created",
        )
        return await self._response_with_stats(project)

    async def list_projects(self, tenant_id: uuid.UUID) -> list[ProjectResponse]:
        projects = await self._project_repo.find_by_tenant(tenant_id)
        if not projects:
            return []
        stats_dict = await self._project_repo.get_stats_batch([p.id for p in projects])
        return [_project_response_with_stats(p, stats_dict) for p in projects]

    async def get_project(self, tenant_id: uuid.UUID, project_id: uuid.UUID) -> ProjectResponse:
        project = await self.get_project_or_404(tenant_id, project_id)
        return await self._response_with_stats(project)

    async def update_project(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        body: ProjectUpdate,
        actor_user_id: uuid.UUID,
    ) -> ProjectResponse:
        project = await self.get_project_or_404(tenant_id, project_id)

        updates: dict[Any, Any] = {}
        if body.name is not None:
            updates[Project.name] = body.name
        if body.description is not None:
            updates[Project.description] = body.description

        if updates:
            await project.set(updates)

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "project.updated",
            "project",
            project.id,
            entity_label=project.name,
            summary="updated",
        )
        reloaded = await self._project_repo.find_by_id(project_id)
        assert reloaded is not None, "project vanished during update"
        return await self._response_with_stats(reloaded)

    async def archive_project(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, actor_user_id: uuid.UUID
    ) -> ProjectResponse:
        project = await self.get_project_or_404(tenant_id, project_id)
        await project.set({Project.archived_at: datetime.now(UTC)})

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "project.archived",
            "project",
            project.id,
            entity_label=project.name,
            summary="archived",
        )
        reloaded = await self._project_repo.find_by_id(project_id)
        assert reloaded is not None, "project vanished during archive"
        return await self._response_with_stats(reloaded)

    async def restore_project(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, actor_user_id: uuid.UUID
    ) -> ProjectResponse:
        project = await self.get_project_or_404(tenant_id, project_id)
        await project.set({Project.archived_at: None})

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "project.restored",
            "project",
            project.id,
            entity_label=project.name,
            summary="restored",
        )
        reloaded = await self._project_repo.find_by_id(project_id)
        assert reloaded is not None, "project vanished during restore"
        return await self._response_with_stats(reloaded)

    async def reset_project(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        confirm_slug: str,
        actor_user_id: uuid.UUID,
    ) -> ProjectResetResponse:
        project = await self.get_project_or_404(tenant_id, project_id)

        if confirm_slug != project.slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slug mismatch: expected '{project.slug}'",
            )

        counts = await self._reset_service.reset_project_data(project, tenant_id, actor_user_id)
        return ProjectResetResponse(
            message=f"Project '{project.name}' has been reset",
            **counts,
        )


def _project_response_with_stats(
    project: Project, stats_dict: dict[uuid.UUID, dict[str, int]]
) -> ProjectResponse:
    resp = ProjectResponse.model_validate(project)
    resp.stats = _stats_for(stats_dict, project.id)
    return resp
