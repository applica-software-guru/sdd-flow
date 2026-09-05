"""Idempotent promotion of the account configured by deployment."""

import logging
import re
from uuid import NAMESPACE_URL, uuid5

from pymongo.errors import DuplicateKeyError

from app.config import settings
from app.models.audit_log_entry import AuditLogEntry
from app.models.base import utcnow
from app.models.user import PlatformRole, User
from app.utils.bson import uuid_to_bin
from app.utils.mongo import raw_collection

logger = logging.getLogger(__name__)


async def promote_configured_super_user(user: User | None = None) -> bool:
    configured_email = settings.SUPER_USER_EMAIL.strip().lower()
    if not configured_email:
        return False

    candidate = user
    if candidate is not None and candidate.email.strip().lower() != configured_email:
        return False
    if candidate is None:
        candidate = await User.find_one(
            {"email": {"$regex": f"^{re.escape(configured_email)}$", "$options": "i"}}
        )
    if candidate is None:
        logger.warning("Configured SUPER_USER account does not exist yet")
        return False
    if candidate.platform_role == PlatformRole.super_user:
        return False

    # Atomic conditional update makes concurrent Cloud Run startups safe.
    result = await raw_collection(User).update_one(
        {"_id": uuid_to_bin(candidate.id), "platformRole": {"$ne": PlatformRole.super_user.value}},
        {"$set": {"platformRole": PlatformRole.super_user.value, "updatedAt": utcnow()}},
    )
    if result.modified_count == 0:
        return False
    candidate.platform_role = PlatformRole.super_user

    # A deterministic event id prevents duplicate audit rows across instances.
    event_id = uuid5(NAMESPACE_URL, f"sdd-flow:super-user-promotion:{candidate.id}")
    try:
        await AuditLogEntry(
            id=event_id,
            tenant_id=None,
            user_id=candidate.id,
            event_type="super_user.promoted_from_environment",
            entity_type="user",
            entity_id=candidate.id,
            summary="User promoted from deployment configuration",
            details={},
        ).insert()
    except DuplicateKeyError:
        pass
    logger.info("Configured account promoted to SUPER_USER")
    return True
