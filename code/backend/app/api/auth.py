import hashlib

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from slowapi import Limiter

from app.config import settings
from app.middleware.auth import get_current_user
from app.models.user import User
from app.repositories import AuthRepository, UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_tokens,
    create_user,
    refresh_access_token,
)
from app.services.password_reset import request_password_reset, reset_password
from fastapi import Cookie


def _get_real_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_get_real_ip, enabled=not settings.TESTING)

router = APIRouter(prefix="/auth", tags=["auth"])


def _cookie_options(max_age_seconds: int) -> dict[str, bool | str | int]:
    return {
        "httponly": True,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "secure": settings.AUTH_COOKIE_SECURE,
        "max_age": max_age_seconds,
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, response: Response):
    user_repo = UserRepository()
    existing = await user_repo.find_by_email(body.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await create_user(body.email, body.password, body.display_name, user_repo=user_repo)
    access_token, refresh_token = await create_tokens(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        **_cookie_options(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        **_cookie_options(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400),
    )
    return user


@router.post("/login", response_model=UserResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, response: Response):
    user = await authenticate_user(body.email, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token, refresh_token = await create_tokens(user.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        **_cookie_options(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        **_cookie_options(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400),
    )
    return user


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    new_access = await refresh_access_token(refresh_token)
    if new_access is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    response.set_cookie(
        key="access_token",
        value=new_access,
        **_cookie_options(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    return {"detail": "Token refreshed"}


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
):
    if refresh_token:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        auth_repo = AuthRepository()
        await auth_repo.delete_refresh_token(token_hash)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Logged out"}


@router.get("/google")
async def google_login():
    if not settings.ENABLE_GOOGLE_OAUTH:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth disabled")
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")
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
async def google_callback(code: str):
    if not settings.ENABLE_GOOGLE_OAUTH:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth disabled")
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")

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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange code")
        tokens = token_resp.json()

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info")
        google_user = userinfo_resp.json()

    from app.services.auth import get_or_create_google_user

    user = await get_or_create_google_user(google_user)
    access_token, refresh_tok = await create_tokens(user.id)

    redirect = RedirectResponse(url="/tenants", status_code=302)
    redirect.set_cookie(
        key="access_token",
        value=access_token,
        **_cookie_options(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    redirect.set_cookie(
        key="refresh_token",
        value=refresh_tok,
        **_cookie_options(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400),
    )
    return redirect


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    await request_password_reset(body.email)
    return {
        "detail": "If an account with that email exists, a password reset link has been sent"
    }


@router.post("/reset-password")
async def reset_password_endpoint(body: ResetPasswordRequest):
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    success = await reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return {"detail": "Password reset successful"}
