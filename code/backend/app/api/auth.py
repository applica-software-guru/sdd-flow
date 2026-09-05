import hashlib
import logging
from collections.abc import Callable
from typing import Literal, ParamSpec, TypeVar, cast

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from slowapi import Limiter

from app.config import settings
from app.dependencies import get_audit_service, get_auth_service
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.audit import AuditService
from app.services.auth import AuthService, ProfileValidationError
from app.services.email_templates import render_template
from app.services.mailer import send_email
from app.services.super_user import promote_configured_super_user

logger = logging.getLogger(__name__)


def _get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_get_real_ip, enabled=not settings.TESTING)

# Typed wrapper around slowapi's untyped decorator factory.
_P = ParamSpec("_P")
_R = TypeVar("_R")


def rate_limit(rule: str) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    return cast(
        "Callable[[Callable[_P, _R]], Callable[_P, _R]]",
        limiter.limit(rule),  # pyright: ignore[reportUnknownMemberType]
    )


router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, key: str, value: str, max_age_seconds: int) -> None:
    """Set an auth cookie with the shared secure options (typed explicitly)."""
    samesite: Literal["lax", "strict", "none"] = settings.AUTH_COOKIE_SAMESITE  # type: ignore[assignment]  # validated in config
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        samesite=samesite,
        secure=settings.AUTH_COOKIE_SECURE,
        max_age=max_age_seconds,
    )


def _set_auth_cookie_pair(response: Response, access_token: str, refresh_token: str) -> None:
    _set_auth_cookie(
        response,
        "access_token",
        access_token,
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    _set_auth_cookie(
        response,
        "refresh_token",
        refresh_token,
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
) -> UserResponse:
    await svc.ensure_email_available(body.email)
    user = await svc.create_user(body.email, body.password, body.display_name)
    await promote_configured_super_user(user)
    access_token, refresh_token = await svc.create_tokens(user.id)

    _set_auth_cookie_pair(response, access_token, refresh_token)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
@rate_limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
    audit: AuditService = Depends(get_audit_service),
) -> UserResponse:
    user = await svc.authenticate_user(body.email, body.password)
    if user is None:
        await audit.log_event(
            tenant_id=None,
            user_id=None,
            event_type="auth.login_failed",
            summary="Invalid credentials",
            details={},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await promote_configured_super_user(user)
    await audit.log_event(
        tenant_id=None,
        user_id=user.id,
        event_type="auth.login_success",
        entity_type="user",
        entity_id=user.id,
        summary="Login successful",
        details={},
    )
    access_token, refresh_token = await svc.create_tokens(user.id)
    _set_auth_cookie_pair(response, access_token, refresh_token)
    return UserResponse.model_validate(user)


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    svc: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    new_access = await svc.refresh_access_token(refresh_token)
    if new_access is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )

    _set_auth_cookie(
        response,
        "access_token",
        new_access,
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"detail": "Token refreshed"}


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    svc: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    if refresh_token:
        await svc.revoke_refresh_token(refresh_token)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Logged out"}


@router.get("/google")
async def google_login() -> RedirectResponse:
    if not settings.ENABLE_GOOGLE_OAUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth disabled"
        )
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured"
        )
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/google/callback")
async def google_callback(
    code: str,
    svc: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    if not settings.ENABLE_GOOGLE_OAUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth disabled"
        )
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured"
        )

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange code"
            )
        tokens = token_resp.json()

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info"
            )
        google_user = userinfo_resp.json()

    user = await svc.get_or_create_google_user(google_user)
    await promote_configured_super_user(user)
    access_token, refresh_tok = await svc.create_tokens(user.id)

    redirect = RedirectResponse(url="/tenants", status_code=302)
    _set_auth_cookie_pair(redirect, access_token, refresh_tok)
    return redirect


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    svc: AuthService = Depends(get_auth_service),
    audit: AuditService = Depends(get_audit_service),
) -> UserResponse:
    old_name = current_user.display_name
    try:
        user = await svc.update_display_name(current_user, body.display_name)
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)

    # Profile-level event: recorded in every tenant the user belongs to
    await audit.log_event_for_user_tenants(
        user_id=user.id,
        event_type="user.profile_updated",
        entity_type="user",
        entity_id=user.id,
        entity_label=user.email,
        summary=f"{old_name} renamed to {user.display_name}",
        details={"old_display_name": old_name, "new_display_name": user.display_name},
    )
    return UserResponse.model_validate(user)


@router.post("/me/change-password")
async def change_password_me(
    body: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    svc: AuthService = Depends(get_auth_service),
    audit: AuditService = Depends(get_audit_service),
) -> dict[str, bool]:
    keep_token_hash = None
    raw_refresh = request.cookies.get("refresh_token")
    if raw_refresh:
        keep_token_hash = hashlib.sha256(raw_refresh.encode()).hexdigest()

    try:
        password_was_set = await svc.change_own_password(
            current_user,
            body.current_password,
            body.new_password,
            keep_token_hash=keep_token_hash,
        )
    except ProfileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)

    # Fire-and-forget confirmation email (never fails the action)
    context = {
        "title": "Your password was changed",
        "display_name": current_user.display_name,
    }
    try:
        await send_email(
            recipient_email=current_user.email,
            subject=render_template("emails/password_changed_subject.txt", **context),
            text_body=render_template("emails/password_changed_text.txt", **context),
            html_body=render_template("emails/password_changed.html", **context),
            log_label="Password changed",
        )
    except Exception:
        logger.exception("Failed to send password-changed email to %s", current_user.email)

    await audit.log_event_for_user_tenants(
        user_id=current_user.id,
        event_type="user.password_changed",
        entity_type="user",
        entity_id=current_user.id,
        entity_label=current_user.email,
        summary="Password changed"
        if not password_was_set
        else "Password set (previously Google-only account)",
        details={"password_set": password_was_set},
    )

    return {"password_set": True}


@router.post("/forgot-password")
@rate_limit("5/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    svc: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    await svc.request_password_reset(body.email)
    return {"detail": "If an account with that email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password_endpoint(
    body: ResetPasswordRequest,
    svc: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    success = await svc.reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return {"detail": "Password reset successful"}
