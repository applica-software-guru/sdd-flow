import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.base import utcnow
from app.repositories import UserRepository, AuthRepository


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


async def create_user(
    email: str,
    password: str,
    display_name: str,
    user_repo: UserRepository = None,
) -> User:
    if user_repo is None:
        user_repo = UserRepository()
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        email_verified=False,
    )
    return await user_repo.save(user)


async def authenticate_user(
    email: str,
    password: str,
    user_repo: UserRepository = None,
) -> User | None:
    if user_repo is None:
        user_repo = UserRepository()
    user = await user_repo.find_by_email(email)
    if user is None or user.password_hash is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _create_token(user_id: uuid.UUID, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": secrets.token_urlsafe(8),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


async def create_tokens(
    user_id: uuid.UUID,
    auth_repo: AuthRepository = None,
) -> tuple[str, str]:
    if auth_repo is None:
        auth_repo = AuthRepository()
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
    await auth_repo.create_refresh_token(rt)
    return access_token, refresh_token_str


async def refresh_access_token(
    refresh_token: str,
    auth_repo: AuthRepository = None,
) -> str | None:
    if auth_repo is None:
        auth_repo = AuthRepository()
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    rt = await auth_repo.find_refresh_token(token_hash)
    if rt is None:
        return None
    expires_at = rt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        await auth_repo.delete_refresh_token(token_hash)
        return None
    access_token = _create_token(
        rt.user_id, "access", timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return access_token


async def get_or_create_google_user(
    google_user_info: dict,
    user_repo: UserRepository = None,
) -> User:
    if user_repo is None:
        user_repo = UserRepository()
    google_id = google_user_info["id"]
    email = google_user_info["email"]
    display_name = google_user_info.get("name", email)
    avatar_url = google_user_info.get("picture")

    user = await user_repo.find_by_google_id(google_id)
    if user is not None:
        return user

    # Check if user exists by email
    user = await user_repo.find_by_email(email)
    if user is not None:
        user.google_id = google_id
        if avatar_url:
            user.avatar_url = avatar_url
        user.email_verified = True
        return await user_repo.save(user)

    user = User(
        email=email,
        display_name=display_name,
        google_id=google_id,
        avatar_url=avatar_url,
        email_verified=True,
    )
    return await user_repo.save(user)
