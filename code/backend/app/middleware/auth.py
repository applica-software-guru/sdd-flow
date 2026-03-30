import hashlib
import uuid
from typing import Callable

from fastapi import Cookie, Depends, Header, HTTPException, Path, status
from jose import JWTError, jwt

from app.config import settings
from app.models.api_key import ApiKey
from app.models.project import Project
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User
from app.models.base import utcnow


async def get_current_user(
    access_token: str | None = Cookie(default=None),
) -> User:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(access_token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if user_id_str is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = await User.get(str(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_current_tenant_member(
    tenant_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
) -> TenantMember:
    member = await TenantMember.find_one(
        {"tenantId": tenant_id, "userId": current_user.id}
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this tenant",
        )
    return member


def require_role(*roles: MemberRole) -> Callable:
    async def dependency(
        member: TenantMember = Depends(get_current_tenant_member),
    ) -> TenantMember:
        if member.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {member.role.value} not authorized. Required: {[r.value for r in roles]}",
            )
        return member

    return dependency


class ApiKeyContext:
    """Project and author resolved from an API key."""
    def __init__(self, project: Project, user_id: uuid.UUID):
        self.project = project
        self.user_id = user_id


async def get_api_key_context(
    authorization: str | None = Header(default=None),
) -> ApiKeyContext:
    """Like get_api_key_project but also returns the user who created the key."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    raw_key = authorization[7:]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = await ApiKey.find_one({"keyHash": key_hash, "revokedAt": None})
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    # Update last_used_at via Beanie partial update
    await api_key.set({ApiKey.last_used_at: utcnow()})

    project = await Project.get(api_key.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return ApiKeyContext(project=project, user_id=api_key.created_by)


async def get_api_key_project(
    authorization: str | None = Header(default=None),
) -> Project:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    raw_key = authorization[7:]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = await ApiKey.find_one({"keyHash": key_hash, "revokedAt": None})
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    # Update last_used_at via Beanie partial update
    await api_key.set({ApiKey.last_used_at: utcnow()})

    project = await Project.get(api_key.project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return project
