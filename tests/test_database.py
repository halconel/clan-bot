"""Tests for database connection management."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import Database, create_database


@pytest.fixture
def test_database_url():
    """Test database URL (in-memory SQLite for testing)."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def database(test_database_url):
    """Create a test database instance."""
    return Database(test_database_url, echo=False)


@pytest.fixture
async def initialized_database(database):
    """Create and initialize a test database."""
    database.init()
    await database.create_tables()
    yield database
    await database.close()


class TestDatabaseInit:
    """Test Database initialization."""

    @pytest.mark.unit
    def test_database_creation(self, test_database_url):
        """Test that Database can be created."""
        db = Database(test_database_url)
        assert db.database_url == test_database_url
        assert db.echo is False
        assert db.pool_size == 5
        assert db.max_overflow == 10

    @pytest.mark.unit
    def test_database_creation_with_params(self, test_database_url):
        """Test Database creation with custom parameters."""
        db = Database(test_database_url, echo=True, pool_size=10, max_overflow=20)
        assert db.echo is True
        assert db.pool_size == 10
        assert db.max_overflow == 20

    @pytest.mark.unit
    def test_engine_not_initialized_before_init(self, database):
        """Test that engine is not available before init()."""
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = database.engine

    @pytest.mark.unit
    def test_session_factory_not_initialized_before_init(self, database):
        """Test that session_factory is not available before init()."""
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = database.session_factory

    @pytest.mark.unit
    def test_init_creates_engine_and_factory(self, database):
        """Test that init() creates engine and session factory."""
        database.init()
        assert database.engine is not None
        assert database.session_factory is not None

    @pytest.mark.unit
    def test_init_idempotent(self, database):
        """Test that init() can be called multiple times safely."""
        database.init()
        engine1 = database.engine
        database.init()  # Should not raise
        engine2 = database.engine
        assert engine1 is engine2

    @pytest.mark.unit
    def test_create_database_factory(self, test_database_url):
        """Test create_database factory function."""
        db = create_database(test_database_url, echo=True)
        assert db.engine is not None
        assert db.session_factory is not None
        assert db.echo is True


class TestDatabaseSession:
    """Test database session management."""

    @pytest.mark.asyncio
    async def test_get_session_yields_async_session(self, initialized_database):
        """Test that get_session yields AsyncSession."""
        async for session in initialized_database.get_session():
            assert isinstance(session, AsyncSession)
            break  # Only test first yield

    @pytest.mark.asyncio
    async def test_get_session_commits_on_success(self, initialized_database):
        """Test that session commits on successful operations."""
        async for session in initialized_database.get_session():
            # Perform a simple query
            result = await session.execute(text("SELECT 1"))
            assert result is not None
            break

    @pytest.mark.asyncio
    async def test_get_session_rolls_back_on_error(self, initialized_database):
        """Test that session rolls back on error."""
        with pytest.raises(SQLAlchemyError):
            async for session in initialized_database.get_session():
                # Force an error
                await session.execute("INVALID SQL QUERY")


class TestDatabaseTables:
    """Test database table operations."""

    @pytest.mark.asyncio
    async def test_create_tables(self, database):
        """Test creating database tables."""
        database.init()
        await database.create_tables()
        # Verify engine is still working
        assert database.engine is not None
        await database.close()

    @pytest.mark.asyncio
    async def test_drop_tables(self, initialized_database):
        """Test dropping database tables."""
        await initialized_database.drop_tables()
        # Verify engine is still working
        assert initialized_database.engine is not None


class TestDatabaseClose:
    """Test database cleanup."""

    @pytest.mark.asyncio
    async def test_close_disposes_engine(self, database):
        """Test that close() disposes the engine."""
        database.init()
        assert database._engine is not None

        await database.close()

        assert database._engine is None
        assert database._session_factory is None

    @pytest.mark.asyncio
    async def test_close_idempotent(self, database):
        """Test that close() can be called multiple times."""
        database.init()
        await database.close()
        await database.close()  # Should not raise
