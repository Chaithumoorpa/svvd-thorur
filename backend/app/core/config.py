from typing import Annotated, List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Values that must never be used to sign tokens in production.
_WEAK_SECRETS = {
    "",
    "test",
    "secret",
    "changeme",
    "your-secret-key-change-in-production",
    "change-this-in-prod-very-secret",
    "dev-secret-key-change-this-in-production-12345678",
}


class Settings(BaseSettings):
    """
    Application settings – the single source of configuration.

    Development: debug mode, verbose logging, docs enabled.
    Production: strict validation (see `_validate_production`).
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # Environment
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

    # Security
    SECRET_KEY: str
    # Roles and active-status are re-read from the database on every request, so a long-ish
    # session (one working day) does not delay revocation.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    # Reverse proxies in front of the API that append to X-Forwarded-For (Next.js rewrite = 1,
    # nginx + Next.js = 2). 0 = trust nobody. The client IP is read from the right, so a
    # client-supplied prefix cannot spoof it.
    TRUSTED_PROXY_HOPS: int = Field(default=0, ge=0, le=5)
    # Public self-registration creates GENERAL_USER accounts (no admin access). The public
    # site has no devotee-account features yet, so it is off unless explicitly enabled.
    ALLOW_PUBLIC_REGISTRATION: bool = False

    # CORS
    CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    # API documentation (defaults to off in production, see docs_enabled)
    ENABLE_DOCS: bool | None = None

    # Security headers / rate limiting (default ON in production, see properties)
    ENABLE_SECURITY_HEADERS: bool | None = None
    ENABLE_RATE_LIMITING: bool | None = None
    RATE_LIMIT_PER_MINUTE: int = 120

    # Alembic
    ALEMBIC_CONFIG: str = "alembic.ini"

    # S3 (gallery photo uploads). Unset = uploads disabled, admins fall back to pasting
    # an image URL. Credentials come from the environment's default AWS chain (an EC2
    # instance role in production; ~/.aws or AWS_* env vars for local use) - never stored here.
    S3_BUCKET_NAME: str | None = None
    AWS_REGION: str = "us-east-1"
    S3_MAX_UPLOAD_MB: int = 8

    # Admin email notifications (contact messages, bookings, donations) via AWS SES.
    # Unset = notifications silently disabled. Same credential chain as S3 above.
    SES_FROM_EMAIL: str | None = None
    ADMIN_NOTIFICATION_EMAIL: str | None = None

    # Razorpay (online payments). Scaffolding only - not yet wired into the
    # donation/ticket booking flows. Unset = the /payments/razorpay endpoints
    # return 503, same opt-in pattern as S3/SES above. Test-mode keys
    # (rzp_test_...) work fine here for development before going live.
    RAZORPAY_KEY_ID: str | None = None
    RAZORPAY_KEY_SECRET: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept a comma-separated string or a list."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):  # JSON list, as used by docker-compose.dev.yml
                import json

                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def _validate_production(self):
        if self.ENV.lower() != "production":
            return self
        if self.SECRET_KEY.lower() in _WEAK_SECRETS or len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be a random value of at least 32 characters in production"
            )
        if "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must not contain '*' in production")
        return self

    # ---- derived flags -------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @property
    def docs_enabled(self) -> bool:
        if self.ENABLE_DOCS is not None:
            return self.ENABLE_DOCS
        return not self.is_production

    @property
    def security_headers_enabled(self) -> bool:
        if self.ENABLE_SECURITY_HEADERS is not None:
            return self.ENABLE_SECURITY_HEADERS
        return self.is_production

    @property
    def rate_limiting_enabled(self) -> bool:
        if self.ENABLE_RATE_LIMITING is not None:
            return self.ENABLE_RATE_LIMITING
        return self.is_production

    @property
    def docs_url(self) -> str | None:
        return "/docs" if self.docs_enabled else None

    @property
    def redoc_url(self) -> str | None:
        return "/redoc" if self.docs_enabled else None

    @property
    def openapi_url(self) -> str | None:
        return "/openapi.json" if self.docs_enabled else None


settings = Settings()

# Convenience exports (kept for existing imports)
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
