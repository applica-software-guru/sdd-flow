from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from app.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.models.base import utcnow
from app.repositories import AuthRepository, UserRepository
from app.services.auth import hash_password
from app.services.email_templates import render_template
from app.services.mailer import send_email


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def request_password_reset(
    email: str,
    auth_repo: AuthRepository = None,
    user_repo: UserRepository = None,
) -> None:
    if auth_repo is None:
        auth_repo = AuthRepository()
    if user_repo is None:
        user_repo = UserRepository()

    user = await user_repo.find_by_email(email)
    if user is None or user.password_hash is None:
        return

    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )
    # Atomic upsert: replace any existing token for this user
    await auth_repo.replace_password_reset_token(user.id, reset_token)

    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{raw_token}"
    context = {
        "title": "Reset your password",
        "cta_label": "Reset password",
        "cta_url": reset_url,
        "display_name": user.display_name,
        "reset_url": reset_url,
        "expires_minutes": settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    }

    await send_email(
        recipient_email=user.email,
        subject=render_template("emails/password_reset_subject.txt", **context),
        text_body=render_template("emails/password_reset_text.txt", **context),
        html_body=render_template("emails/password_reset.html", **context),
        log_label="Password reset",
    )


async def reset_password(
    token: str,
    new_password: str,
    auth_repo: AuthRepository = None,
    user_repo: UserRepository = None,
) -> bool:
    if auth_repo is None:
        auth_repo = AuthRepository()
    if user_repo is None:
        user_repo = UserRepository()

    token_hash = _hash_token(token)
    # Atomic find-and-delete: returns the doc only if it exists and hasn't expired
    reset_doc = await auth_repo.find_and_delete_valid_reset_token(token_hash)
    if reset_doc is None:
        return False

    user_id = reset_doc.get("userId")
    if user_id is None:
        return False

    import uuid
    from bson.binary import Binary, UuidRepresentation
    try:
        if isinstance(user_id, Binary):
            uid = user_id.as_uuid(uuid_representation=UuidRepresentation.STANDARD)
        else:
            uid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError):
        return False

    user = await user_repo.find_by_id(uid)
    if user is None:
        return False

    user.password_hash = hash_password(new_password)
    user.email_verified = True
    await user_repo.save(user)

    # Revoke all refresh tokens for security (SEC-001)
    await auth_repo.revoke_all_refresh_tokens(uid)

    return True
