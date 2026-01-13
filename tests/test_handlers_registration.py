"""Integration tests for registration handlers."""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, Message, PhotoSize, User

from bot.handlers.registration import cmd_register, process_nickname, process_screenshot
from bot.states.registration import RegistrationStates
from config.settings import Settings, TelegramConfig, DatabaseConfig, StorageConfig, LoggingConfig
from database.database import Database
from database.repository import PlayerRepository


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
def storage():
    """Create FSM storage."""
    return MemoryStorage()


@pytest.fixture
def user():
    """Create test user."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
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
async def fsm_context(storage, user, chat):
    """Create FSM context."""
    bot_id = 123456
    key = StorageKey(bot_id=bot_id, chat_id=chat.id, user_id=user.id)
    return FSMContext(storage=storage, key=key)


def create_message(text: str, user: User, chat: Chat, **kwargs) -> Message:
    """Helper to create message object."""
    return Message(
        message_id=1,
        date=datetime.now().timestamp(),
        chat=chat,
        from_user=user,
        text=text,
        **kwargs,
    )


class TestRegisterCommand:
    """Test /register command."""

    @pytest.mark.asyncio
    async def test_register_new_user(
        self, database: Database, test_settings: Settings, fsm_context: FSMContext, user: User, chat: Chat
    ):
        """Test registration of a new user."""
        message = create_message("/register", user, chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_register(message, fsm_context)

        # Check that bot sent response
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "игровой никнейм" in call_text.lower()

        # Check FSM state
        state = await fsm_context.get_state()
        assert state == RegistrationStates.waiting_for_nickname

    @pytest.mark.asyncio
    async def test_register_already_registered(
        self, database: Database, test_settings: Settings, fsm_context: FSMContext, user: User, chat: Chat
    ):
        """Test that already registered user cannot register again."""
        # Add user to database
        from models.player import Player

        async for session in database.get_session():
            repo = PlayerRepository(session)
            player = Player(
                telegram_id=user.id,
                username=f"@{user.username}",
                nickname="ExistingPlayer",
                screenshot_path="/path/to/screenshot.jpg",
                registration_date=datetime.now().strftime("%Y-%m-%d"),
                status="Активен",
            )
            await repo.add_player(player)
            break

        message = create_message("/register", user, chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_register(message, fsm_context)

        # Check that bot sent rejection message
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "уже зарегистрированы" in call_text.lower()

        # Check FSM state was not set
        state = await fsm_context.get_state()
        assert state is None

    @pytest.mark.asyncio
    async def test_register_pending_application(
        self, database: Database, test_settings: Settings, fsm_context: FSMContext, user: User, chat: Chat
    ):
        """Test that user with pending application cannot register again."""
        # Add pending registration
        from models.player import PendingRegistration

        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = PendingRegistration(
                telegram_id=user.id,
                username=f"@{user.username}",
                nickname="PendingPlayer",
                screenshot_path="/path/to/screenshot.jpg",
            )
            await repo.save_pending(pending)
            break

        message = create_message("/register", user, chat)
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        await cmd_register(message, fsm_context)

        # Check that bot sent rejection message
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "уже подана" in call_text.lower()


class TestNicknameProcess:
    """Test nickname processing."""

    @pytest.mark.asyncio
    async def test_valid_nickname(self, fsm_context: FSMContext, user: User, chat: Chat):
        """Test processing valid nickname."""
        await fsm_context.set_state(RegistrationStates.waiting_for_nickname)

        message = create_message("TestPlayer", user, chat)
        message.answer = AsyncMock()

        await process_nickname(message, fsm_context)

        # Check that bot requested screenshot
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "скриншот" in call_text.lower()

        # Check FSM state changed
        state = await fsm_context.get_state()
        assert state == RegistrationStates.waiting_for_screenshot

        # Check nickname was saved
        data = await fsm_context.get_data()
        assert data["nickname"] == "TestPlayer"

    @pytest.mark.asyncio
    async def test_invalid_nickname_too_short(self, fsm_context: FSMContext, user: User, chat: Chat):
        """Test processing nickname that is too short."""
        await fsm_context.set_state(RegistrationStates.waiting_for_nickname)

        message = create_message("AB", user, chat)
        message.answer = AsyncMock()

        await process_nickname(message, fsm_context)

        # Check that bot sent error message
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "3 до 20 символов" in call_text

        # Check FSM state did not change
        state = await fsm_context.get_state()
        assert state == RegistrationStates.waiting_for_nickname

    @pytest.mark.asyncio
    async def test_invalid_nickname_special_chars(self, fsm_context: FSMContext, user: User, chat: Chat):
        """Test processing nickname with invalid characters."""
        await fsm_context.set_state(RegistrationStates.waiting_for_nickname)

        message = create_message("Test@Player!", user, chat)
        message.answer = AsyncMock()

        await process_nickname(message, fsm_context)

        # Check that bot sent error message
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "только буквы" in call_text.lower()


class TestScreenshotProcess:
    """Test screenshot processing."""

    @pytest.mark.asyncio
    async def test_valid_screenshot(
        self, database: Database, test_settings: Settings, fsm_context: FSMContext, user: User, chat: Chat, tmp_path
    ):
        """Test processing valid screenshot."""
        await fsm_context.set_state(RegistrationStates.waiting_for_screenshot)
        await fsm_context.update_data(nickname="TestPlayer")

        # Create message with photo
        photo = PhotoSize(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            width=800,
            height=600,
            file_size=50000,
        )
        message = create_message("", user, chat)
        message.photo = [photo]
        message.answer = AsyncMock()
        message.bot = MagicMock()
        message.bot.get = MagicMock(side_effect=lambda key: database if key == "db" else test_settings)

        # Mock file download
        mock_file = MagicMock()
        mock_file.file_path = "photos/test.jpg"
        message.bot.get_file = AsyncMock(return_value=mock_file)
        message.bot.download_file = AsyncMock(return_value=b"fake_image_data")
        message.bot.send_photo = AsyncMock()

        await process_screenshot(message, fsm_context)

        # Check that screenshot was downloaded
        message.bot.get_file.assert_called_once_with(photo.file_id)
        message.bot.download_file.assert_called_once()

        # Check that confirmation was sent
        message.answer.assert_called()

        # Check that notification was sent to admin
        message.bot.send_photo.assert_called_once()

        # Check FSM state was cleared
        state = await fsm_context.get_state()
        assert state is None

        # Check pending registration was saved
        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = await repo.get_pending(user.id)
            assert pending is not None
            assert pending.nickname == "TestPlayer"
            assert pending.username == f"@{user.username}"
            break

    @pytest.mark.asyncio
    async def test_no_photo_sent(self, fsm_context: FSMContext, user: User, chat: Chat):
        """Test when user sends message without photo."""
        await fsm_context.set_state(RegistrationStates.waiting_for_screenshot)

        message = create_message("Some text", user, chat)
        message.photo = None
        message.answer = AsyncMock()

        await process_screenshot(message, fsm_context)

        # Check that bot sent error message
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "скриншот" in call_text.lower()

        # Check FSM state did not change
        state = await fsm_context.get_state()
        assert state == RegistrationStates.waiting_for_screenshot
