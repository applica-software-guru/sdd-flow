import enum
from pymongo import IndexModel
from pydantic import Field

from app.models.base import BaseDocument


class DefaultRole(str, enum.Enum):
    member = "member"
    viewer = "viewer"


class Tenant(BaseDocument):
    name: str
    slug: str
    default_role: DefaultRole = Field(default=DefaultRole.member, alias="defaultRole")

    class Settings:
        name = "tenants"
        indexes = [
            IndexModel("slug", unique=True),
        ]
