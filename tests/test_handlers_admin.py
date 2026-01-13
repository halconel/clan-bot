"""Integration tests for admin handlers."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import CallbackQuery, Chat, Message, User

from bot.handlers.admin import cmd_exclude, cmd_list, cmd_pending, process_approve, process_reject
from config.settings import DatabaseConfig, LoggingConfig, Settings, StorageConfig, TelegramConfig
from database.database import Database
from database.repository import PlayerRepository
from models.player import PendingRegistration, Player


@pytest.fixture
def test_settings(tmp_path):
    """Create test settings."""
    screenshots_dir = tmp_path / "screenshots"
    screenshots_dir.mkdir()

    return Settings(
        telegram=TelegramConfig(
            bot_token="123456:TEST_TOKEN",
            leader_telegram_id=999999999,
        ),
        database=DatabaseConfig(
            database_url="sqlite+aiosqlite:///:memory:",
        ),
        storage=StorageConfig(
            screenshots_dir=str(screenshots_dir),
            temp_storage_file=str(tmp_path / "pending.json"),
        ),
        logging=LoggingConfig(
            log_level="INFO",
            log_file=str(tmp_path / "test.log"),
        ),
    )


@pytest.fixture
async def database(test_settings):
    """Create test database."""
    db = Database(test_settings.database.database_url, echo=False)
    db.init()
    await db.create_tables()
    yield db
    await db.close()


@pytest.fixture
def user():
    """Create test user."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        username="testuser",
    )


@pytest.fixture
def admin_user(test_settings):
    """Create admin user."""
    return User(
        id=test_settings.telegram.leader_telegram_id,
        is_bot=False,
        first_name="Admin",
        username="admin",
    )


@pytest.fixture
def chat():
    """Create test chat."""
    return Chat(id=123456789, type="private")


@pytest.fixture
def admin_chat(test_settings):
    """Create admin chat."""
    return Chat(id=test_settings.telegram.leader_telegram_id, type="private")


def create_message(text: str, user: User, chat: Chat) -> Message:
    """Helper to create message object."""
    return Message(
        message_id=1,
        date=datetime.now().timestamp(),
        chat=chat,
        from_user=user,
        text=text,
    )


def create_callback(data: str, user: User, message: Message) -> CallbackQuery:
    """Helper to create callback query object."""
    return CallbackQuery(
        id="test_callback",
        from_user=user,
        data=data,
        message=message,
        chat_instance="test_instance",
    )


class TestApproveCallback:
    """Test approve callback handler."""

    @pytest.mark.asyncio
    async def test_approve_by_admin(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test approving registration by admin."""
        # Add pending registration
        pending_user_id = 123456789
        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = PendingRegistration(
                telegram_id=pending_user_id,
                username="@testuser",
                nickname="TestPlayer",
                screenshot_path="/path/to/screenshot.jpg",
            )
            await repo.save_pending(pending)
            break

        # Create callback
        message = create_message("", admin_user, admin_chat)
        message.caption = "Test pending application"
        message.edit_caption = AsyncMock()
        callback = create_callback(f"approve:{pending_user_id}", admin_user, message)
        callback.answer = AsyncMock()
        callback.bot = MagicMock()
        callback.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)
        callback.bot.send_message = AsyncMock()

        await process_approve(callback)

        # Check that approval was processed
        callback.answer.assert_called_once()
        assert "одобрена" in callback.answer.call_args[0][0].lower()

        # Check that message was edited
        message.edit_caption.assert_called_once()

        # Check that user was notified
        callback.bot.send_message.assert_called_once()
        assert callback.bot.send_message.call_args[1]["chat_id"] == pending_user_id

        # Check that player was added to database
        async for session in database.get_session():
            repo = PlayerRepository(session)
            player = await repo.get_player(pending_user_id)
            assert player is not None
            assert player.nickname == "TestPlayer"
            assert player.status == "Активен"

            # Check that pending was removed
            pending = await repo.get_pending(pending_user_id)
            assert pending is None
            break

    @pytest.mark.asyncio
    async def test_approve_by_non_admin(
        self, database: Database, test_settings: Settings, user: User, chat: Chat
    ):
        """Test that non-admin cannot approve."""
        message = create_message("", user, chat)
        callback = create_callback("approve:123456789", user, message)
        callback.answer = AsyncMock()
        callback.bot = MagicMock()
        callback.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await process_approve(callback)

        # Check that rejection was sent
        callback.answer.assert_called_once()
        assert "нет прав" in callback.answer.call_args[1]["text"].lower()


class TestRejectCallback:
    """Test reject callback handler."""

    @pytest.mark.asyncio
    async def test_reject_by_admin(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test rejecting registration by admin."""
        # Add pending registration
        pending_user_id = 123456789
        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = PendingRegistration(
                telegram_id=pending_user_id,
                username="@testuser",
                nickname="TestPlayer",
                screenshot_path="/path/to/screenshot.jpg",
            )
            await repo.save_pending(pending)
            break

        # Create callback
        message = create_message("", admin_user, admin_chat)
        message.caption = "Test pending application"
        message.edit_caption = AsyncMock()
        callback = create_callback(f"reject:{pending_user_id}", admin_user, message)
        callback.answer = AsyncMock()
        callback.bot = MagicMock()
        callback.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)
        callback.bot.send_message = AsyncMock()

        await process_reject(callback)

        # Check that rejection was processed
        callback.answer.assert_called_once()
        assert "отклонена" in callback.answer.call_args[0][0].lower()

        # Check that pending was removed
        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = await repo.get_pending(pending_user_id)
            assert pending is None
            break


class TestPendingCommand:
    """Test /pending command."""

    @pytest.mark.asyncio
    async def test_pending_with_applications(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test showing pending applications."""
        # Add pending registrations
        async for session in database.get_session():
            repo = PlayerRepository(session)
            for i in range(3):
                pending = PendingRegistration(
                    telegram_id=123456789 + i,
                    username=f"@user{i}",
                    nickname=f"Player{i}",
                    screenshot_path=f"/path/to/screenshot{i}.jpg",
                )
                await repo.save_pending(pending)
            break

        message = create_message("/pending", admin_user, admin_chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_pending(message)

        # Check that response was sent
        message.answer.assert_called_once()
        response_text = message.answer.call_args[0][0]
        assert "ожидающие заявки" in response_text.lower()
        assert "Player0" in response_text
        assert "Player1" in response_text
        assert "Player2" in response_text

    @pytest.mark.asyncio
    async def test_pending_empty(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test showing pending when there are no applications."""
        message = create_message("/pending", admin_user, admin_chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_pending(message)

        # Check that empty message was sent
        message.answer.assert_called_once()
        response_text = message.answer.call_args[0][0]
        assert "нет ожидающих" in response_text.lower()


class TestListCommand:
    """Test /list command."""

    @pytest.mark.asyncio
    async def test_list_with_players(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test showing list of players."""
        # Add players
        async for session in database.get_session():
            repo = PlayerRepository(session)
            for i in range(3):
                player = Player(
                    telegram_id=123456789 + i,
                    username=f"@player{i}",
                    nickname=f"Player{i}",
                    screenshot_path=f"/path{i}.jpg",
                    registration_date=datetime.now().strftime("%Y-%m-%d"),
                    status="Активен",
                )
                await repo.add_player(player)

            # Add excluded player
            excluded_player = Player(
                telegram_id=999999999,
                username="@excluded",
                nickname="ExcludedPlayer",
                screenshot_path="/path_excluded.jpg",
                registration_date=datetime.now().strftime("%Y-%m-%d"),
                status="Отчислен",
            )
            await repo.add_player(excluded_player)
            break

        message = create_message("/list", admin_user, admin_chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_list(message)

        # Check that response was sent
        message.answer.assert_called_once()
        response_text = message.answer.call_args[0][0]
        assert "всего игроков: 4" in response_text.lower()
        assert "активные (3)" in response_text.lower()
        assert "Player0" in response_text
        assert "отчисленные (1)" in response_text.lower()
        assert "ExcludedPlayer" in response_text


class TestExcludeCommand:
    """Test /exclude command."""

    @pytest.mark.asyncio
    async def test_exclude_player(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test excluding a player."""
        # Add player
        player_id = 123456789
        async for session in database.get_session():
            repo = PlayerRepository(session)
            player = Player(
                telegram_id=player_id,
                username="@testplayer",
                nickname="TestPlayer",
                screenshot_path="/path.jpg",
                registration_date=datetime.now().strftime("%Y-%m-%d"),
                status="Активен",
            )
            await repo.add_player(player)
            break

        message = create_message("/exclude @testplayer Нарушение правил", admin_user, admin_chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)
        message.bot.send_message = AsyncMock()

        await cmd_exclude(message)

        # Check that success message was sent
        message.answer.assert_called_once()
        response_text = message.answer.call_args[0][0]
        assert "отчислен" in response_text.lower()

        # Check that player was excluded in database
        async for session in database.get_session():
            repo = PlayerRepository(session)
            player = await repo.get_player(player_id)
            assert player.status == "Отчислен"
            assert player.exclusion_reason == "Нарушение правил"
            break

    @pytest.mark.asyncio
    async def test_exclude_invalid_format(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test exclude with invalid command format."""
        message = create_message("/exclude @testplayer", admin_user, admin_chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_exclude(message)

        # Check that error message was sent
        message.answer.assert_called_once()
        response_text = message.answer.call_args[0][0]
        assert "неверный формат" in response_text.lower()

    @pytest.mark.asyncio
    async def test_exclude_non_existing_player(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test excluding player that doesn't exist."""
        message = create_message("/exclude @nonexistent Причина", admin_user, admin_chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_exclude(message)

        # Check that error message was sent
        message.answer.assert_called_once()
        response_text = message.answer.call_args[0][0]
        assert "не найден" in response_text.lower()
