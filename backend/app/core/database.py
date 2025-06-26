"""
Database configuration and session management for the medical chatbot.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator

from .config import settings

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
    poolclass=StaticPool if "sqlite" in settings.database_url else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

# Redis connection
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_db() -> Generator:
    """
    Dependency to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> redis.Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis client
    """
    return redis_client


class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    def create_tables():
        """Create all database tables."""
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def drop_tables():
        """Drop all database tables."""
        Base.metadata.drop_all(bind=engine)
    
    @staticmethod
    def reset_database():
        """Reset database by dropping and recreating tables."""
        DatabaseManager.drop_tables()
        DatabaseManager.create_tables()


async def init_db():
    """Initialize database and create tables."""
    DatabaseManager.create_tables()


async def close_db():
    """Close database connections."""
    engine.dispose()
    redis_client.close()
