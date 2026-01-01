"""
Migration validation utilities for Alembic.

Ensures migration safety, especially in production environments.
"""
import logging
import sys
from typing import List, Tuple
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


class MigrationValidationError(Exception):
    """Raised when migration validation fails."""
    pass


def get_migration_heads(alembic_config_path: str) -> List[str]:
    """
    Get all migration head revisions.
    
    Args:
        alembic_config_path: Path to alembic.ini file
        
    Returns:
        List of head revision IDs
    """
    try:
        alembic_cfg = Config(alembic_config_path)
        script = ScriptDirectory.from_config(alembic_cfg)
        heads = script.get_revisions("heads")
        return [head.revision for head in heads]
    except Exception as e:
        logger.error(f"Failed to get migration heads: {e}")
        raise MigrationValidationError(f"Failed to get migration heads: {e}")


def get_current_revision(database_url: str) -> str | None:
    """
    Get current database revision.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Current revision ID or None if no migrations applied
    """
    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
        return current_rev
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        raise MigrationValidationError(f"Failed to get current revision: {e}")


def validate_single_head(alembic_config_path: str) -> Tuple[bool, List[str]]:
    """
    Validate that there is only a single migration head.
    
    Args:
        alembic_config_path: Path to alembic.ini file
        
    Returns:
        Tuple of (is_valid, list_of_heads)
    """
    heads = get_migration_heads(alembic_config_path)
    is_valid = len(heads) <= 1
    return is_valid, heads


def validate_migrations(
    alembic_config_path: str,
    database_url: str,
    strict: bool = False
) -> None:
    """
    Validate migration state.
    
    Args:
        alembic_config_path: Path to alembic.ini file
        database_url: Database connection URL
        strict: If True, raise exception on validation failure (production mode)
        
    Raises:
        MigrationValidationError: If validation fails in strict mode
    """
    logger.info("Validating migration state...")
    
    # Check for multiple heads
    is_valid, heads = validate_single_head(alembic_config_path)
    
    if not is_valid:
        error_msg = (
            f"Multiple migration heads detected: {heads}\n"
            f"This indicates a merge conflict in migrations.\n"
            f"Please merge the migration branches using:\n"
            f"  alembic merge {' '.join(heads)}\n"
            f"Then create a new migration to resolve the conflict."
        )
        
        if strict:
            logger.error(error_msg)
            logger.error("PRODUCTION MODE: Cannot start with multiple migration heads!")
            raise MigrationValidationError(error_msg)
        else:
            logger.warning(error_msg)
            logger.warning("DEVELOPMENT MODE: Multiple heads allowed, but should be resolved.")
    else:
        logger.info(f"✓ Single migration head: {heads[0] if heads else 'none'}")
    
    # Check current revision
    try:
        current_rev = get_current_revision(database_url)
        if current_rev:
            logger.info(f"✓ Current database revision: {current_rev}")
            
            # Check if current revision is at head
            if current_rev not in heads:
                warning_msg = (
                    f"Database revision {current_rev} is not at head {heads}\n"
                    f"Migrations may need to be applied."
                )
                if strict:
                    logger.warning(warning_msg)
                else:
                    logger.info(warning_msg)
        else:
            logger.info("Database has no migrations applied yet")
    except Exception as e:
        logger.warning(f"Could not check current revision: {e}")


def check_migrations_on_startup(
    alembic_config_path: str,
    database_url: str,
    is_production: bool = False
) -> None:
    """
    Check migrations on application startup.
    
    Args:
        alembic_config_path: Path to alembic.ini file
        database_url: Database connection URL
        is_production: Whether running in production mode
    """
    try:
        validate_migrations(
            alembic_config_path=alembic_config_path,
            database_url=database_url,
            strict=is_production
        )
    except MigrationValidationError as e:
        logger.critical("Migration validation failed!")
        logger.critical(str(e))
        if is_production:
            logger.critical("Exiting due to migration validation failure in production.")
            sys.exit(1)
        else:
            logger.warning("Continuing in development mode despite migration issues.")
