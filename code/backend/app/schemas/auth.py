import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import PlatformRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    display_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str | None = None
    new_password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    avatar_url: str | None = None
    email_verified: bool
    has_password: bool = False
    google_linked: bool = False
    platform_role: PlatformRole = PlatformRole.user
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str = "access"
