from typing import Annotated, List, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

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

    # Database: either one DATABASE_URL (docker-compose, CI, tests) or the discrete
    # DB_* parts (managed RDS - see _assemble_database_url). DATABASE_URL wins if both.
    DATABASE_URL: str | None = None
    DB_HOST: str | None = None
    DB_PORT: int = 5432
    DB_NAME: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    # libpq sslmode / CA bundle. RDS: verify-full + the AWS RDS global CA bundle
    # (baked into the Lambda image, see backend/Dockerfile.lambda).
    DB_SSLMODE: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] | None = None
    DB_SSLROOTCERT: str | None = None
    # Fail fast instead of hanging until the Lambda timeout when the DB is unreachable
    # (e.g. a security group silently dropping packets).
    DB_CONNECT_TIMEOUT: int = Field(default=10, ge=1)
    # Per-process connection pool. On Lambda each container serves one request at a
    # time, so keep this tiny there - max connections = concurrency x (size + overflow).
    DB_POOL_SIZE: int = Field(default=5, ge=1)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    SQLALCHEMY_ECHO: bool = False

    # Security
    SECRET_KEY: str
    # Roles and active-status are re-read from the database on every request, so this
    # only bounds how long a *stolen* token stays usable. A session stays alive as long
    # as the user is actually doing something - the frontend silently calls /auth/refresh
    # every so often while there's activity (see lib/api.ts) - and simply expires after
    # this many minutes of no activity at all.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
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

    # Hard cap on request body size (every endpoint here is JSON text - no file
    # bytes ever pass through this backend, those go straight to S3 via a
    # presigned URL) - rejects an oversized body before it's buffered into memory.
    MAX_REQUEST_BODY_BYTES: int = 1_000_000

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

    # Public site origin, used to build links inside outgoing emails (password reset, etc).
    FRONTEND_BASE_URL: str = "https://svvdthorur.org"

    # Where the temple is - festival dates are computed for local sunrise,
    # moonrise etc. (app/services/panchang.py). Thorrur, Mahabubabad district.
    TEMPLE_LATITUDE: float = 17.5857
    TEMPLE_LONGITUDE: float = 79.6578
    TEMPLE_ELEVATION: float = 250.0

    # Cloudflare Turnstile (bot/brute-force challenge on login, register, forgot-password).
    # Unset = verification is skipped rather than failing closed - matches SES/S3 above,
    # so local dev and any environment without keys configured still works.
    TURNSTILE_SECRET_KEY: str | None = None

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
    def _assemble_database_url(self):
        # URL.create escapes the password - RDS-generated ones routinely contain
        # '@', '/', ':' etc. that would corrupt a hand-concatenated URL. SSL options and
        # the connect timeout go into the URL's query string (not connect_args) so every
        # engine built from DATABASE_URL - app, Alembic, the startup check - gets them.
        if self.DATABASE_URL:
            url = make_url(self.DATABASE_URL)
        else:
            missing = [n for n in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD") if not getattr(self, n)]
            if missing:
                raise ValueError(f"Set DATABASE_URL, or all of DB_HOST/DB_NAME/DB_USER/DB_PASSWORD (missing: {', '.join(missing)})")
            url = URL.create(
                "postgresql",
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                database=self.DB_NAME,
            )
        if url.get_backend_name() == "postgresql":
            opts = {
                "sslmode": self.DB_SSLMODE,
                "sslrootcert": self.DB_SSLROOTCERT,
                "connect_timeout": str(self.DB_CONNECT_TIMEOUT),
            }
            url = url.update_query_dict({k: v for k, v in opts.items() if v and k not in url.query})
        self.DATABASE_URL = url.render_as_string(hide_password=False)
        return self

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
        if not self.TURNSTILE_SECRET_KEY:
            # Unset makes TurnstileService a silent no-op (see its docstring) -
            # fine for local dev, but in production it would mean every
            # CAPTCHA-gated form (registration, login, forgot-password, ...)
            # accepts every submission with no bot/abuse check at all, with
            # nothing in the logs to say so. Refuse to boot instead.
            raise ValueError("TURNSTILE_SECRET_KEY must be set in production")
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
