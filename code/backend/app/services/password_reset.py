from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth import hash_password
from app.services.email_templates import render_template
from app.services.mailer import send_email


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def request_password_reset(db: AsyncSession, email: str) -> None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or user.password_hash is None:
        return

    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))

    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(reset_token)
    await db.flush()

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


async def reset_password(db: AsyncSession, token: str, new_password: str) -> bool:
    token_hash = _hash_token(token)
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    reset_token = result.scalar_one_or_none()
    if reset_token is None:
        return False

    if reset_token.used_at is not None:
        return False

    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return False

    user_result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return False

    user.password_hash = hash_password(new_password)
    user.email_verified = True
    reset_token.used_at = datetime.now(timezone.utc)

    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.flush()
    return True
