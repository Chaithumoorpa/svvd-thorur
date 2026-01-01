"""
Debug utilities for development environment.

These utilities should ONLY be used in development mode.
"""
import logging
from typing import Any, Dict
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def log_db_state(db: Session, table_name: str) -> None:
    """
    Log the current state of a database table (DEVELOPMENT ONLY).
    
    Args:
        db: Database session
        table_name: Name of the table to inspect
    """
    try:
        result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()
        logger.debug(f"Table '{table_name}' has {count} rows")
        
        # Get first few rows
        result = db.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
        rows = result.fetchall()
        logger.debug(f"First 5 rows of '{table_name}':")
        for row in rows:
            logger.debug(f"  {dict(row._mapping)}")
    except Exception as e:
        logger.error(f"Failed to inspect table '{table_name}': {e}")


def log_auth_decision(
    user_id: int | None,
    required_role: str,
    has_permission: bool,
    endpoint: str
) -> None:
    """
    Log authentication/authorization decisions (DEVELOPMENT ONLY).
    
    Args:
        user_id: ID of the user making the request
        required_role: Role required for the endpoint
        has_permission: Whether the user has permission
        endpoint: The endpoint being accessed
    """
    status = "✓ ALLOWED" if has_permission else "✗ DENIED"
    logger.debug(
        f"Auth Decision: {status} | "
        f"User: {user_id or 'anonymous'} | "
        f"Required: {required_role} | "
        f"Endpoint: {endpoint}"
    )


def log_request_body(body: Dict[str, Any], endpoint: str) -> None:
    """
    Log request body for debugging (DEVELOPMENT ONLY).
    
    Args:
        body: Request body dictionary
        endpoint: The endpoint receiving the request
    """
    logger.debug(f"Request to {endpoint}:")
    for key, value in body.items():
        # Mask sensitive fields
        if key.lower() in ["password", "secret", "token", "api_key"]:
            value = "***MASKED***"
        logger.debug(f"  {key}: {value}")


def log_response_body(body: Dict[str, Any], endpoint: str, status_code: int) -> None:
    """
    Log response body for debugging (DEVELOPMENT ONLY).
    
    Args:
        body: Response body dictionary
        endpoint: The endpoint sending the response
        status_code: HTTP status code
    """
    logger.debug(f"Response from {endpoint} ({status_code}):")
    logger.debug(f"  {body}")


def check_migration_status() -> Dict[str, Any]:
    """
    Check Alembic migration status (DEVELOPMENT ONLY).
    
    Returns:
        Dictionary with migration status information
    """
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        from app.core.config import settings
        
        # Get Alembic config
        alembic_cfg = Config(settings.ALEMBIC_CONFIG)
        script = ScriptDirectory.from_config(alembic_cfg)
        
        # Get current revision from database
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
        
        # Get head revision(s)
        heads = script.get_revisions("heads")
        
        status = {
            "current_revision": current_rev,
            "head_revisions": [head.revision for head in heads],
            "multiple_heads": len(heads) > 1,
            "up_to_date": current_rev in [head.revision for head in heads],
        }
        
        logger.debug(f"Migration Status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Failed to check migration status: {e}")
        return {"error": str(e)}


def log_startup_info() -> None:
    """
    Log startup information (DEVELOPMENT ONLY).
    """
    from app.core.config import settings
    
    logger.info("=" * 60)
    logger.info("🚀 Temple Management Backend - DEVELOPMENT MODE")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    logger.info(f"SQLAlchemy Echo: {settings.SQLALCHEMY_ECHO}")
    logger.info(f"API Docs: {settings.docs_url or 'disabled'}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info("=" * 60)
    
    # Check migration status
    migration_status = check_migration_status()
    if migration_status.get("multiple_heads"):
        logger.warning("⚠️  Multiple migration heads detected!")
        logger.warning("   This is allowed in development but must be resolved before production.")
    elif migration_status.get("up_to_date"):
        logger.info("✓ Database migrations are up to date")
    else:
        logger.warning("⚠️  Database may need migration")
