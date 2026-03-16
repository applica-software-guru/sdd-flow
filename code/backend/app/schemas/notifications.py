import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import PaginatedResponse


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    event_type: str
    entity_type: str
    entity_id: uuid.UUID
    title: str
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(PaginatedResponse[NotificationResponse]):
    pass
