import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator, validator

# Values that must never be used as the JWT signing key in production.
# They are published in this repository, so anyone could forge admin tokens.
INSECURE_SECRET_KEYS = {
    "",
    "your-secret-key-change-in-production",
    "change-this-in-prod-very-secret",
    "dev-secret-key-change-this-in-production-12345678",
}
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """
    Application settings with environment-aware configuration.
    
    Development: Debug mode, verbose logging, relaxed CORS
    Production: Minimal logging, strict CORS, security hardening
    """
    
    # Environment
    ENV: str = Field(default="development", env="ENV")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    SQLALCHEMY_ECHO: bool = Field(default=False, env="SQLALCHEMY_ECHO")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Documentation
    ENABLE_DOCS: bool = Field(default=True, env="ENABLE_DOCS")
    
    # Security Headers (Production)
    ENABLE_SECURITY_HEADERS: bool = Field(default=False, env="ENABLE_SECURITY_HEADERS")
    
    # Rate Limiting (Production)
    ENABLE_RATE_LIMITING: bool = Field(default=False, env="ENABLE_RATE_LIMITING")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Number of reverse proxies in front of this app that append to
    # X-Forwarded-For (e.g. 1 for Nginx/Caddy -> app). 0 means "trust nobody":
    # the header is ignored and the TCP peer address is used. Never trust the
    # left-most entry - clients control it.
    TRUSTED_PROXY_HOPS: int = Field(default=0, ge=0, le=5, env="TRUSTED_PROXY_HOPS")

    # Alembic
    ALEMBIC_CONFIG: str = Field(default="alembic.ini", env="ALEMBIC_CONFIG")

    @model_validator(mode="after")
    def reject_insecure_secret_in_production(self):
        """Fail fast instead of running production with a guessable signing key."""
        if self.ENV.lower() == "production":
            if (
                self.SECRET_KEY in INSECURE_SECRET_KEYS
                or len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH
            ):
                raise ValueError(
                    "SECRET_KEY is empty, a published default, or shorter than "
                    f"{MIN_SECRET_KEY_LENGTH} characters. Generate one with: "
                    "python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
        return self

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENV.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENV.lower() == "production"
    
    @property
    def docs_url(self) -> str | None:
        """Return docs URL if enabled, None otherwise."""
        return "/docs" if self.ENABLE_DOCS else None
    
    @property
    def redoc_url(self) -> str | None:
        """Return redoc URL if enabled, None otherwise."""
        return "/redoc" if self.ENABLE_DOCS else None
    
    @property
    def openapi_url(self) -> str | None:
        """Return OpenAPI URL if enabled, None otherwise."""
        return "/openapi.json" if self.ENABLE_DOCS else None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Convenience exports
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
