"""Database connection and session management for ContextVault."""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .config import get_database_url, settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Database engine configuration
def create_database_engine() -> Engine:
    """Create and configure the database engine."""
    database_url = get_database_url()
    
    # Configure engine based on database type
    engine_kwargs = {}
    
    if database_url.startswith("sqlite:"):
        # SQLite-specific configuration
        engine_kwargs.update({
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 20,
            },
            "echo": settings.log_level == "DEBUG",
            "future": True,
        })
    else:
        # PostgreSQL/MySQL configuration
        engine_kwargs.update({
            "echo": settings.log_level == "DEBUG",
            "future": True,
            "pool_pre_ping": True,
            "pool_recycle": 300,
        })
    
    engine = create_engine(database_url, **engine_kwargs)
    
    # SQLite-specific optimizations
    if database_url.startswith("sqlite:"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and integrity."""
            cursor = dbapi_connection.cursor()
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Optimize for speed vs safety (adjust as needed)
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            cursor.close()
    
    return engine


# Global engine and session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database sessions.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions outside of FastAPI.
    
    Usage:
        with get_db_context() as db:
            # Use db session
            pass
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_tables() -> None:
    """Drop all database tables (use with caution!)."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


def check_database_connection() -> bool:
    """
    Check if the database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get information about the database.
    
    Returns:
        dict: Database information including URL, driver, and connection status
    """
    try:
        db_url = get_database_url()
        # Remove credentials from URL for logging
        safe_url = db_url
        if "@" in db_url:
            parts = db_url.split("@")
            if len(parts) == 2:
                protocol_user = parts[0].split("://")
                if len(protocol_user) == 2:
                    safe_url = f"{protocol_user[0]}://***:***@{parts[1]}"
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            connected = result == 1
    except Exception:
        connected = False
    
    return {
        "url": safe_url,
        "driver": engine.dialect.name,
        "connected": connected,
        "pool_size": getattr(engine.pool, "size", "N/A"),
        "pool_checked_in": getattr(engine.pool, "checkedin", "N/A"),
        "pool_checked_out": getattr(engine.pool, "checkedout", "N/A"),
    }


def init_database() -> None:
    """
    Initialize the database with tables and basic setup.
    This is the main function to call for database initialization.
    """
    logger.info("Initializing database...")
    
    # Check connection
    if not check_database_connection():
        raise RuntimeError("Cannot connect to database")
    
    # Create tables
    create_tables()
    
    # Log database info
    db_info = get_database_info()
    logger.info(f"Database initialized: {db_info['driver']} at {db_info['url']}")


# For backwards compatibility and imports
def get_db():
    """Legacy function name - use get_db_session() instead."""
    return get_db_session()
