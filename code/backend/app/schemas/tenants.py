import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.tenant import DefaultRole
from app.models.tenant_member import MemberRole


class TenantCreate(BaseModel):
    name: str
    slug: str
    default_role: DefaultRole = DefaultRole.member


class TenantUpdate(BaseModel):
    name: str | None = None
    default_role: DefaultRole | None = None


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    default_role: DefaultRole
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    display_name: str
    role: MemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class InvitationCreate(BaseModel):
    email: str
    role: MemberRole = MemberRole.member


class InvitationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    role: MemberRole
    token: str
    expires_at: datetime
    accepted_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
