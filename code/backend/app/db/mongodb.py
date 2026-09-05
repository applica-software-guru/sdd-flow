import typing

import certifi
from beanie import (
    init_beanie,  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
)
from pymongo import AsyncMongoClient

from app.models.api_key import ApiKey
from app.models.assignment_history import AssignmentHistory
from app.models.audit_log_entry import AuditLogEntry
from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.comment import Comment
from app.models.document_file import DocumentFile
from app.models.notification import Notification
from app.models.notification_email_log import NotificationEmailLog
from app.models.notification_preference import NotificationPreference
from app.models.password_reset_token import PasswordResetToken
from app.models.project import Project
from app.models.refresh_token import RefreshToken
from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.models.worker import Worker
from app.models.worker_job import WorkerJob
from app.models.worker_job_message import WorkerJobMessage


async def init_db(mongodb_url: str, default_db: str = "sdd"):
    tls_kwargs: dict[str, typing.Any] = (
        {"tlsCAFile": certifi.where()} if mongodb_url.startswith("mongodb+srv://") else {}
    )
    client = AsyncMongoClient(
        mongodb_url,
        tz_aware=True,
        maxPoolSize=50,
        minPoolSize=5,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=3000,
        **tls_kwargs,
    )
    try:
        db = client.get_default_database()
    except Exception:
        db = client[default_db]
    await init_beanie(  # pyright: ignore[reportUnknownMemberType]
        database=db,
        document_models=[
            User,
            Tenant,
            TenantMember,
            TenantInvitation,
            Project,
            ApiKey,
            DocumentFile,
            ChangeRequest,
            Bug,
            Comment,
            AuditLogEntry,
            AssignmentHistory,
            Notification,
            NotificationPreference,
            NotificationEmailLog,
            RefreshToken,
            PasswordResetToken,
            Worker,
            WorkerJob,
            WorkerJobMessage,
        ],
    )
    return client
