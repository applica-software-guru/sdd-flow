"""API key domain service."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.models.api_key import ApiKey
from app.repositories import ApiKeyRepository
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services.audit import AuditService
from app.services.projects import ProjectService


class ApiKeyService:
    def __init__(
        self,
        project_service: ProjectService,
        api_key_repo: ApiKeyRepository,
        audit_service: AuditService,
    ) -> None:
        self._project_service = project_service
        self._api_key_repo = api_key_repo
        self._audit_service = audit_service

    async def create_api_key(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        body: ApiKeyCreate,
        actor_user_id: uuid.UUID,
    ) -> ApiKeyCreatedResponse:
        await self._project_service.get_project_or_404(tenant_id, project_id)

        raw_key = f"sdd_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:12]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = ApiKey(
            project_id=project_id,
            name=body.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            created_by=actor_user_id,
        )
        await self._api_key_repo.create(api_key)

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "api_key.created",
            "api_key",
            api_key.id,
            entity_label=api_key.name,
            summary="created",
        )

        base = ApiKeyResponse.model_validate(api_key, from_attributes=True)
        return ApiKeyCreatedResponse(**base.model_dump(), full_key=raw_key)

    async def list_api_keys(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[ApiKeyResponse]:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        keys = await self._api_key_repo.find_by_project(project_id)
        return [ApiKeyResponse.model_validate(k, from_attributes=True) for k in keys]

    async def revoke_api_key(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        key_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> None:
        await self._project_service.get_project_or_404(tenant_id, project_id)

        api_key = await self._api_key_repo.find_by_id(key_id)
        if api_key is None or api_key.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

        await api_key.set({ApiKey.revoked_at: datetime.now(UTC)})

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "api_key.revoked",
            "api_key",
            api_key.id,
            entity_label=api_key.name,
            summary="revoked",
        )
