import logging
import sys
import os

def setup_logging():
    """
    Configure production-ready logging for the FastAPI application.
    
    Logging Levels:
    - DEBUG: Detailed information for diagnosing problems (JWT decoding, role checks)
    - INFO: General informational messages (user login, admin operations)
    - WARNING: Warning messages (authentication failures, access denied)
    - ERROR: Error messages (exceptions, failures)
    
    Environment Variables:
    - LOG_LEVEL: Set logging level (default: INFO in production, DEBUG in development)
    - ENV: Set environment (production/development)
    """
    
    env = os.getenv("ENV", "development")
    log_level_str = os.getenv("LOG_LEVEL", "DEBUG" if env == "development" else "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup information
    root_logger.info(f"Logging configured: level={log_level_str}, env={env}")
    
    return root_logger
