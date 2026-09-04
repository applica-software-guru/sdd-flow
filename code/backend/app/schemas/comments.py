import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.users import UserBrief


class CommentCreate(BaseModel):
    body: str


class CommentUpdate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    author_id: uuid.UUID
    author: UserBrief | None = None
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
