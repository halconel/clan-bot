"""Database connection and session management with dependency injection."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database.models import Base

logger = logging.getLogger(__name__)


class Database:
    """Database manager with dependency injection support."""

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL (must use asyncpg driver)
            echo: Whether to echo SQL statements to logs
            pool_size: Connection pool size
            max_overflow: Max connections beyond pool_size
        """
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine instance."""
        if self._engine is None:
            raise RuntimeError("Database engine not initialized. Call init() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory instance."""
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized. Call init() first.")
        return self._session_factory

    def init(self) -> None:
        """Initialize the database engine and session factory."""
        if self._engine is not None:
            logger.warning("Database engine already initialized")
            return

        try:
            # Build engine kwargs
            engine_kwargs = {"echo": self.echo}

            # Only add pool settings for non-SQLite databases
            if not self.database_url.startswith("sqlite"):
                engine_kwargs.update(
                    {
                        "pool_pre_ping": True,  # Verify connections before using
                        "pool_size": self.pool_size,
                        "max_overflow": self.max_overflow,
                    }
                )

            self._engine = create_async_engine(self.database_url, **engine_kwargs)
            logger.info("Database engine initialized successfully")

            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,  # Don't expire objects after commit
                autocommit=False,
                autoflush=False,
            )
            logger.info("Session factory initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def create_tables(self) -> None:
        """Create all database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def drop_tables(self) -> None:
        """Drop all database tables. Use with caution!"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise

    async def close(self) -> None:
        """Close database engine and dispose of connection pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async generator that yields database sessions.

        Usage:
            async for session in db.get_session():
                # Use session here
                pass

        Yields:
            AsyncSession instance
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()


def create_database(database_url: str, echo: bool = False) -> Database:
    """
    Factory function to create and initialize a Database instance.

    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements to logs

    Returns:
        Initialized Database instance
    """
    db = Database(database_url, echo=echo)
    db.init()
    return db
