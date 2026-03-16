import uuid

from pydantic import BaseModel


class SearchResult(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    title: str
    snippet: str | None = None
    project_id: uuid.UUID | None = None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str
