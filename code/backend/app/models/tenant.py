import enum

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class DefaultRole(enum.StrEnum):
    member = "member"
    viewer = "viewer"


class Tenant(BaseDocument):
    name: str
    slug: str
    default_role: DefaultRole = Field(default=DefaultRole.member)

    class Settings:
        name = "tenants"
        indexes = [
            IndexModel("slug", unique=True),
        ]
