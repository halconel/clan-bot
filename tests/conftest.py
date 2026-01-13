"""Shared fixtures for all tests."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from config.settings import (
    DatabaseConfig,
    LoggingConfig,
    Settings,
    StorageConfig,
    TelegramConfig,
)
from database.database import Database


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
def admin_chat(test_settings):
    """Create admin chat."""
    return Chat(id=test_settings.telegram.leader_telegram_id, type="private")


@pytest.fixture
def bot():
    """Create mock bot."""
    mock_bot = MagicMock(spec=Bot)
    mock_bot.id = 123456
    mock_bot.token = "123456:TEST_TOKEN"
    mock_bot.send_message = AsyncMock()
    mock_bot.send_photo = AsyncMock()
    mock_bot.get_file = AsyncMock()
    mock_bot.download_file = AsyncMock()
    return mock_bot


@pytest.fixture
async def fsm_context(storage, user, chat):
    """Create FSM context."""
    bot_id = 123456
    key = StorageKey(bot_id=bot_id, chat_id=chat.id, user_id=user.id)
    return FSMContext(storage=storage, key=key)


# Helper functions for creating test objects


def create_message(text: str, user: User, chat: Chat, **kwargs) -> Message:
    """Helper to create message object.

    Args:
        text: Message text
        user: User who sent the message
        chat: Chat where message was sent
        **kwargs: Additional message fields (e.g., photo)

    Returns:
        Message object
    """
    return Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text=text,
        **kwargs,
    )


def create_callback(data: str, user: User, message: Message) -> CallbackQuery:
    """Helper to create callback query object.

    Args:
        data: Callback data
        user: User who triggered callback
        message: Message with inline keyboard

    Returns:
        CallbackQuery object
    """
    return CallbackQuery(
        id="test_callback",
        from_user=user,
        data=data,
        message=message,
        chat_instance="test_instance",
    )


def create_update(message: Message = None, callback_query: CallbackQuery = None) -> Update:
    """Helper to create update object.

    Args:
        message: Optional message
        callback_query: Optional callback query

    Returns:
        Update object
    """
    return Update(
        update_id=1,
        message=message,
        callback_query=callback_query,
    )
