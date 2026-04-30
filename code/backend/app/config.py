from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator

_WEAK_SECRETS = {"change-me-in-production", "secret", "changeme", "supersecret"}


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017/sddflow"
    TESTING: bool = False
    JWT_SECRET: str = "change-me-in-production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    APP_DOMAIN: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    ENABLE_GOOGLE_OAUTH: bool = False
    FRONTEND_URL: str = "http://localhost:3002"
    AUTH_COOKIE_SECURE: bool = False
    AUTH_COOKIE_SAMESITE: str = "lax"
    MAIL_PROVIDER: str = "log"
    MAIL_FROM_EMAIL: str = "noreply@sdd-flow.local"
    MAIL_FROM_NAME: str = "SDD Flow"
    MAIL_SMTP_HOST: str = ""
    MAIL_SMTP_PORT: int = 587
    MAIL_SMTP_USERNAME: str = ""
    MAIL_SMTP_PASSWORD: str = ""
    MAIL_SMTP_USE_TLS: bool = True
    BREVO_API_KEY: str = ""

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        if value in _WEAK_SECRETS:
            raise ValueError("JWT_SECRET is too weak")
        return value

    @field_validator("AUTH_COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalized

    @field_validator("MAIL_PROVIDER")
    @classmethod
    def validate_mail_provider(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"log", "smtp", "brevo"}:
            raise ValueError("MAIL_PROVIDER must be one of: log, smtp, brevo")
        return normalized

    @model_validator(mode="after")
    def derive_frontend_url_from_domain(self):
        if not self.FRONTEND_URL and self.APP_DOMAIN:
            self.FRONTEND_URL = f"https://{self.APP_DOMAIN}"
        if self.AUTH_COOKIE_SAMESITE == "none" and not self.AUTH_COOKIE_SECURE:
            raise ValueError("AUTH_COOKIE_SECURE must be true when AUTH_COOKIE_SAMESITE is 'none'")
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
