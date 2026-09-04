"""Auth service: registration, tokens, profile, password flows.

Pure crypto helpers (`hash_password`, `verify_password`,
`display_name_from_email`) remain module-level functions; every flow that
touches repositories lives in `AuthService`.
"""

import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from fastapi import HTTPException, status
from jose import jwt

from app.config import settings
from app.models.base import utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import AuthRepository, UserRepository
from app.services.email_templates import render_template
from app.services.mailer import send_email


class ProfileValidationError(Exception):
    """Raised when a profile update or password change is invalid."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, stored: str) -> bool:
    if not plain or not stored:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed stored hash (e.g. seed/test data) — treat as no match
        return False


def display_name_from_email(email: str) -> str:
    """Derive a human-readable display name from an email address.

    Used as fallback when a Google account provides no name: the email local
    part is split on `.`, `_`, `-`, `+` and title-cased, so
    `mario.rossi@acme.com` becomes `Mario Rossi` instead of the raw email
    (which would overflow tight UI slots).
    """
    local_part = email.split("@", 1)[0]
    parts = [p for p in re.split(r"[._\-+]+", local_part) if p]
    derived = " ".join(p[0].upper() + p[1:] for p in parts)
    return derived or email


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _create_token(user_id: uuid.UUID, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "jti": secrets.token_urlsafe(8),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        auth_repo: AuthRepository,
    ) -> None:
        self._user_repo = user_repo
        self._auth_repo = auth_repo

    # ── registration & tokens ─────────────────────────────────────────────────

    async def ensure_email_available(self, email: str) -> None:
        """Raise 409 when the email is already registered."""
        existing = await self._user_repo.find_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )

    async def create_user(self, email: str, password: str, display_name: str) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            email_verified=False,
        )
        return await self._user_repo.save(user)

    async def create_tokens(self, user_id: uuid.UUID) -> tuple[str, str]:
        access_token = _create_token(
            user_id, "access", timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token_str = _create_token(
            user_id, "refresh", timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self._auth_repo.create_refresh_token(rt)
        return access_token, refresh_token_str

    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await self._user_repo.find_by_email(email)
        if user is None or user.password_hash is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def refresh_access_token(self, refresh_token: str) -> str | None:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        rt = await self._auth_repo.find_refresh_token(token_hash)
        if rt is None:
            return None
        expires_at = rt.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            await self._auth_repo.delete_refresh_token(token_hash)
            return None
        return _create_token(
            rt.user_id, "access", timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Delete the refresh token identified by its raw value (logout)."""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self._auth_repo.delete_refresh_token(token_hash)

    async def get_or_create_google_user(self, google_user_info: dict[str, Any]) -> User:
        google_id = google_user_info["id"]
        email = google_user_info["email"]
        display_name = google_user_info.get("name") or display_name_from_email(email)
        avatar_url = google_user_info.get("picture")

        user = await self._user_repo.find_by_google_id(google_id)
        if user is not None:
            return user

        # Google accounts are pre-verified: match an existing unverified
        # registration by email, otherwise create a new account.
        user = await self._user_repo.find_by_email(email)
        if user is not None:
            user.google_id = google_id
            user.avatar_url = avatar_url
            user.email_verified = True
            if user.password_hash is None:
                user.display_name = display_name
            return await self._user_repo.save(user)

        user = User(
            email=email,
            display_name=display_name,
            google_id=google_id,
            avatar_url=avatar_url,
            email_verified=True,
        )
        return await self._user_repo.save(user)

    # ── profile & password ────────────────────────────────────────────────────

    async def update_display_name(self, user: User, display_name: str) -> User:
        trimmed = display_name.strip()
        if not trimmed:
            raise ProfileValidationError("Display name cannot be empty")
        if len(trimmed) > 80:
            raise ProfileValidationError("Display name must be at most 80 characters")
        user.display_name = trimmed
        return await self._user_repo.save(user)

    async def change_own_password(
        self,
        user: User,
        current_password: str | None,
        new_password: str,
        keep_token_hash: str | None = None,
    ) -> bool:
        """Change (or set, for Google-only users) the user's own password.

        Returns True when a *new* password was set (Google-only account without
        a previous password), False when an existing password was changed.
        Raises ProfileValidationError for invalid input.

        All refresh tokens except `keep_token_hash` are revoked so the current
        session stays alive while other devices are signed out.
        """
        if len(new_password) < 8:
            raise ProfileValidationError("Password must be at least 8 characters")

        had_password = user.password_hash is not None
        if had_password:
            stored_hash = user.password_hash
            if (
                not current_password
                or stored_hash is None
                or not verify_password(current_password, stored_hash)
            ):
                raise ProfileValidationError("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        await self._user_repo.save(user)

        if keep_token_hash is not None:
            await self._auth_repo.revoke_other_refresh_tokens(user.id, keep_token_hash)
        else:
            await self._auth_repo.revoke_all_refresh_tokens(user.id)

        return not had_password

    # ── password reset (forgot-password flow) ─────────────────────────────────

    async def request_password_reset(self, email: str) -> None:
        user = await self._user_repo.find_by_email(email)
        if user is None or user.password_hash is None:
            return

        from app.models.password_reset_token import PasswordResetToken

        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
        # Atomic upsert: replace any existing token for this user
        await self._auth_repo.replace_password_reset_token(user.id, reset_token)

        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{raw_token}"
        context: dict[str, Any] = {
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

    async def reset_password(self, token: str, new_password: str) -> bool:
        token_hash = _hash_token(token)
        # Atomic find-and-delete: returns the doc only if it exists and hasn't expired
        reset_doc = await self._auth_repo.find_and_delete_valid_reset_token(token_hash)
        if reset_doc is None:
            return False

        user_id = reset_doc.get("userId")
        if user_id is None:
            return False

        from bson.binary import Binary, UuidRepresentation

        try:
            if isinstance(user_id, Binary):
                uid = user_id.as_uuid(uuid_representation=UuidRepresentation.STANDARD)
            else:
                uid = uuid.UUID(str(user_id))
        except (ValueError, AttributeError):
            return False

        user = await self._user_repo.find_by_id(uid)
        if user is None:
            return False

        user.password_hash = hash_password(new_password)
        user.email_verified = True
        await self._user_repo.save(user)

        # Revoke all refresh tokens for security (SEC-001)
        await self._auth_repo.revoke_all_refresh_tokens(uid)

        return True
