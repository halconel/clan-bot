"""Tests for database repository layer."""

from datetime import datetime

import pytest

from database.database import Database
from database.repository import PlayerRepository
from models.player import PendingRegistration, Player


@pytest.fixture
def test_database_url():
    """Test database URL (in-memory SQLite for testing)."""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def database(test_database_url):
    """Create and initialize test database."""
    db = Database(test_database_url, echo=False)
    db.init()
    await db.create_tables()
    yield db
    await db.close()


@pytest.fixture
async def session(database):
    """Get a database session for testing."""
    async for sess in database.get_session():
        yield sess


@pytest.fixture
def repository(session):
    """Create a repository instance."""
    return PlayerRepository(session)


@pytest.fixture
def sample_player():
    """Sample player data."""
    return Player(
        telegram_id=123456789,
        username="@testuser",
        nickname="TestNick",
        screenshot_path="/path/to/screenshot.jpg",
        registration_date=datetime.now().strftime("%Y-%m-%d"),
        status="Активен",
        added_by="bot",
        notes="Test player",
    )


@pytest.fixture
def sample_pending():
    """Sample pending registration data."""
    return PendingRegistration(
        telegram_id=987654321,
        username="@pendinguser",
        nickname="PendingNick",
        screenshot_path="/path/to/pending.jpg",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


class TestAddPlayer:
    """Test adding players to database."""

    @pytest.mark.asyncio
    async def test_add_player_success(self, repository, sample_player):
        """Test successfully adding a player."""
        added_player = await repository.add_player(sample_player)

        assert added_player.telegram_id == sample_player.telegram_id
        assert added_player.username == sample_player.username
        assert added_player.nickname == sample_player.nickname

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="SQLite aiosqlite has issues with RETURNING after IntegrityError")
    async def test_add_duplicate_player_fails(self, database):
        """Test that adding duplicate player raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        player = Player(
            telegram_id=123456789,
            username="@testuser",
            nickname="TestNick",
        )

        # Add player in first session
        async for session in database.get_session():
            repo = PlayerRepository(session)
            await repo.add_player(player)
            break

        # Try to add same player in new session
        with pytest.raises(IntegrityError):
            async for session in database.get_session():
                repo = PlayerRepository(session)
                await repo.add_player(player)
                break


class TestGetPlayer:
    """Test retrieving players from database."""

    @pytest.mark.asyncio
    async def test_get_existing_player(self, repository, sample_player):
        """Test retrieving an existing player."""
        await repository.add_player(sample_player)

        retrieved = await repository.get_player(sample_player.telegram_id)
        assert retrieved is not None
        assert retrieved.telegram_id == sample_player.telegram_id
        assert retrieved.username == sample_player.username

    @pytest.mark.asyncio
    async def test_get_non_existing_player(self, repository):
        """Test retrieving non-existing player returns None."""
        retrieved = await repository.get_player(999999)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_check_player_exists(self, repository, sample_player):
        """Test checking if player exists."""
        assert await repository.check_player_exists(sample_player.telegram_id) is False

        await repository.add_player(sample_player)

        assert await repository.check_player_exists(sample_player.telegram_id) is True


class TestGetAllPlayers:
    """Test retrieving all players."""

    @pytest.mark.asyncio
    async def test_get_all_players_empty(self, repository):
        """Test getting all players when database is empty."""
        players = await repository.get_all_players()
        assert len(players) == 0
        assert isinstance(players, list)

    @pytest.mark.asyncio
    async def test_get_all_players_with_data(self, repository):
        """Test getting all players with multiple players."""
        player1 = Player(
            telegram_id=111,
            username="@user1",
            nickname="Nick1",
            screenshot_path="/path1.jpg",
        )
        player2 = Player(
            telegram_id=222,
            username="@user2",
            nickname="Nick2",
            screenshot_path="/path2.jpg",
        )

        await repository.add_player(player1)
        await repository.add_player(player2)

        players = await repository.get_all_players()
        assert len(players) == 2
        telegram_ids = [p.telegram_id for p in players]
        assert 111 in telegram_ids
        assert 222 in telegram_ids


class TestUpdatePlayerStatus:
    """Test updating player status."""

    @pytest.mark.asyncio
    async def test_update_status_success(self, repository, sample_player):
        """Test successfully updating player status."""
        await repository.add_player(sample_player)

        result = await repository.update_player_status(sample_player.telegram_id, "Неактивен")
        assert result is True

        updated = await repository.get_player(sample_player.telegram_id)
        assert updated.status == "Неактивен"

    @pytest.mark.asyncio
    async def test_update_status_non_existing_player(self, repository):
        """Test updating status of non-existing player returns False."""
        result = await repository.update_player_status(999999, "Неактивен")
        assert result is False


class TestExcludePlayer:
    """Test player exclusion functionality."""

    @pytest.mark.asyncio
    async def test_exclude_player_success(self, repository, sample_player):
        """Test successfully excluding a player."""
        await repository.add_player(sample_player)

        result = await repository.exclude_player(
            sample_player.telegram_id, reason="Test exclusion", excluded_by="test_admin"
        )
        assert result is True

        # Verify player status changed
        excluded = await repository.get_player(sample_player.telegram_id)
        assert excluded.status == "Отчислен"
        assert excluded.exclusion_reason == "Test exclusion"
        assert excluded.excluded_by == "test_admin"
        assert excluded.exclusion_date is not None

    @pytest.mark.asyncio
    async def test_exclude_non_existing_player(self, repository):
        """Test excluding non-existing player returns False."""
        result = await repository.exclude_player(999999, "Reason", "admin")
        assert result is False


class TestGetExcludedPlayers:
    """Test retrieving excluded players."""

    @pytest.mark.asyncio
    async def test_get_excluded_players_empty(self, repository):
        """Test getting excluded players when none exist."""
        excluded = await repository.get_excluded_players()
        assert len(excluded) == 0

    @pytest.mark.asyncio
    async def test_get_excluded_players_with_data(self, repository):
        """Test getting excluded players."""
        player1 = Player(telegram_id=111, username="@user1", nickname="Nick1")
        player2 = Player(telegram_id=222, username="@user2", nickname="Nick2")
        player3 = Player(telegram_id=333, username="@user3", nickname="Nick3")

        await repository.add_player(player1)
        await repository.add_player(player2)
        await repository.add_player(player3)

        # Exclude two players
        await repository.exclude_player(player1.telegram_id, "Reason 1", "admin")
        await repository.exclude_player(player2.telegram_id, "Reason 2", "admin")

        excluded = await repository.get_excluded_players()
        assert len(excluded) == 2
        telegram_ids = [p.telegram_id for p in excluded]
        assert 111 in telegram_ids
        assert 222 in telegram_ids
        assert 333 not in telegram_ids


class TestPendingRegistrations:
    """Test pending registration operations."""

    @pytest.mark.asyncio
    async def test_save_pending(self, repository, sample_pending):
        """Test saving a pending registration."""
        saved = await repository.save_pending(sample_pending)

        assert saved.telegram_id == sample_pending.telegram_id
        assert saved.username == sample_pending.username

    @pytest.mark.asyncio
    async def test_get_pending(self, repository, sample_pending):
        """Test retrieving a pending registration."""
        await repository.save_pending(sample_pending)

        retrieved = await repository.get_pending(sample_pending.telegram_id)
        assert retrieved is not None
        assert retrieved.telegram_id == sample_pending.telegram_id

    @pytest.mark.asyncio
    async def test_get_pending_by_username(self, repository, sample_pending):
        """Test retrieving pending by username."""
        await repository.save_pending(sample_pending)

        retrieved = await repository.get_pending_by_username(sample_pending.username)
        assert retrieved is not None
        assert retrieved.username == sample_pending.username

    @pytest.mark.asyncio
    async def test_remove_pending(self, repository, sample_pending):
        """Test removing a pending registration."""
        await repository.save_pending(sample_pending)
        assert await repository.get_pending(sample_pending.telegram_id) is not None

        result = await repository.remove_pending(sample_pending.telegram_id)
        assert result is True

        assert await repository.get_pending(sample_pending.telegram_id) is None

    @pytest.mark.asyncio
    async def test_get_all_pending(self, repository):
        """Test getting all pending registrations."""
        pending1 = PendingRegistration(
            telegram_id=111,
            username="@pending1",
            nickname="Pending1",
            screenshot_path="/path1.jpg",
        )
        pending2 = PendingRegistration(
            telegram_id=222,
            username="@pending2",
            nickname="Pending2",
            screenshot_path="/path2.jpg",
        )

        await repository.save_pending(pending1)
        await repository.save_pending(pending2)

        all_pending = await repository.get_all_pending()
        assert len(all_pending) == 2
