"""Integration tests for registration flow through Dispatcher."""

from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, Update, User

from bot.handlers import admin, common, registration
from config.settings import Settings
from database.database import Database


@pytest.fixture(scope="module")
def module_storage():
    """Create shared storage for all tests in module."""
    return MemoryStorage()


@pytest.fixture(scope="module")
def module_dispatcher(module_storage):
    """Create single dispatcher for entire module."""
    dp = Dispatcher(storage=module_storage)

    # Register handlers once
    dp.include_router(common.router)
    dp.include_router(registration.router)
    dp.include_router(admin.router)

    return dp


@pytest.fixture
async def dispatcher(database, test_settings, module_dispatcher):
    """Configure dispatcher with test dependencies."""
    # Update DI dependencies for this specific test
    module_dispatcher["db"] = database
    module_dispatcher["settings"] = test_settings

    return module_dispatcher


def create_update(
    message: Optional[Message] = None, callback_query: Optional[CallbackQuery] = None
) -> Update:
    """Create Update object."""
    return Update(
        update_id=1,
        message=message,
        callback_query=callback_query,
    )


def create_message(text: str, user_id: int = 123456789, username: str = "testuser") -> Message:
    """Create Message object."""
    user = User(
        id=user_id,
        is_bot=False,
        first_name="Test",
        username=username,
    )
    chat = Chat(id=user_id, type="private")

    return Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text=text,
    )


def create_callback_query(
    data: str, user_id: int = 123456789, username: str = "testuser"
) -> CallbackQuery:
    """Create CallbackQuery object."""
    user = User(
        id=user_id,
        is_bot=False,
        first_name="Test",
        username=username,
    )
    chat = Chat(id=user_id, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text="",
    )

    return CallbackQuery(
        id="callback_123",
        from_user=user,
        chat_instance="instance_123",
        data=data,
        message=message,
    )


class TestFullRegistrationFlow:
    """Test full registration flow through Dispatcher."""

    @pytest.mark.asyncio
    async def test_start_command_flow(self, dispatcher: Dispatcher, bot: MagicMock):
        """Test /start command through dispatcher."""
        message = create_message("/start")
        update = create_update(message=message)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await dispatcher.feed_update(bot, update)

            # Check that welcome message was sent
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
            assert "добро пожаловать" in call_text.lower()
            assert "the born ussr" in call_text.lower()
            assert "/register" in call_text

    @pytest.mark.asyncio
    async def test_help_command_flow(self, dispatcher: Dispatcher, bot: MagicMock):
        """Test /help command through dispatcher."""
        message = create_message("/help")
        update = create_update(message=message)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await dispatcher.feed_update(bot, update)

            # Check that help text was sent
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
            assert "команды" in call_text.lower()

    @pytest.mark.asyncio
    async def test_register_command_flow(self, dispatcher: Dispatcher, bot: MagicMock):
        """Test /register command through dispatcher."""
        message = create_message("/register")
        update = create_update(message=message)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await dispatcher.feed_update(bot, update)

            # Check that captcha was shown (2 messages: explanation + question)
            assert mock_answer.call_count == 2

            # First message should be captcha explanation
            first_call_text = mock_answer.call_args_list[0][0][0]
            assert "безопасност" in first_call_text.lower()

            # Second message should be captcha question
            second_call_kwargs = mock_answer.call_args_list[1][1]
            assert "reply_markup" in second_call_kwargs

    @pytest.mark.asyncio
    async def test_full_registration_flow_with_fsm(
        self, dispatcher: Dispatcher, bot: MagicMock, database: Database
    ):
        """Test complete registration flow: /register -> captcha -> nickname -> screenshot -> pending."""
        user_id = 987654321
        username = "newplayer"

        # Step 1: /register command - shows captcha
        message1 = create_message("/register", user_id=user_id, username=username)
        update1 = create_update(message=message1)

        # Mock generate_captcha to return predictable question
        from utils.captcha import CaptchaQuestion

        test_captcha = CaptchaQuestion(
            question="Сколько будет 2 + 2?",
            correct_answer="4",
            wrong_answers=["3", "5"],
        )

        with (
            patch("bot.handlers.registration.generate_captcha", return_value=test_captcha),
            patch.object(Message, "answer", new=AsyncMock()) as mock_answer,
        ):
            await dispatcher.feed_update(bot, update1)
            # Should send captcha (2 messages: explanation + question)
            assert mock_answer.call_count == 2
            assert "безопасност" in mock_answer.call_args_list[0][0][0].lower()

        # Step 2: Answer captcha correctly
        callback1 = create_callback_query("captcha:4", user_id=user_id, username=username)
        update1_callback = create_update(callback_query=callback1)

        with (
            patch.object(Message, "answer", new=AsyncMock()) as mock_answer,
            patch.object(Message, "edit_text", new=AsyncMock()) as mock_edit,
            patch.object(CallbackQuery, "answer", new=AsyncMock()),
        ):
            await dispatcher.feed_update(bot, update1_callback)

            # Should edit message and ask for nickname
            mock_edit.assert_called_once()
            mock_answer.assert_called_once()
            assert "никнейм" in mock_answer.call_args[0][0].lower()

        # Step 3: Send nickname
        message2 = create_message("TestPlayer123", user_id=user_id, username=username)
        update2 = create_update(message=message2)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await dispatcher.feed_update(bot, update2)
            mock_answer.assert_called_once()
            assert "скриншот" in mock_answer.call_args[0][0].lower()

        # Step 3: Send screenshot (photo)
        photo = PhotoSize(
            file_id="test_file_123",
            file_unique_id="unique_123",
            width=800,
            height=600,
            file_size=50000,
        )
        message3 = create_message("", user_id=user_id, username=username)
        # Use object.__setattr__ to set photo on frozen model
        object.__setattr__(message3, "photo", [photo])

        # Mock bot methods for file download
        mock_file = MagicMock()
        mock_file.file_path = "photos/test.jpg"
        bot.get_file.return_value = mock_file
        bot.download_file.return_value = b"fake_image_data"

        # Mock bot attribute on message
        object.__setattr__(message3, "_bot", bot)

        update3 = create_update(message=message3)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await dispatcher.feed_update(bot, update3)

            # Check that registration was completed
            mock_answer.assert_called()

            # Verify admin notification was sent
            bot.send_photo.assert_called_once()

        # Step 4: Verify pending registration was saved
        from database.repository import PlayerRepository

        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = await repo.get_pending(user_id)
            assert pending is not None
            assert pending.nickname == "TestPlayer123"
            assert pending.username == f"@{username}"


class TestAdminFlow:
    """Test admin commands flow through Dispatcher."""

    @pytest.mark.asyncio
    async def test_pending_command_flow(
        self, dispatcher: Dispatcher, bot: MagicMock, database: Database, test_settings: Settings
    ):
        """Test /pending command through dispatcher."""
        # Add a pending registration first
        from database.repository import PlayerRepository
        from models.player import PendingRegistration

        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = PendingRegistration(
                telegram_id=111222333,
                username="@testuser",
                nickname="TestPlayer",
                screenshot_path="/path/to/screenshot.jpg",
            )
            await repo.save_pending(pending)

        # Admin sends /pending
        admin_id = test_settings.telegram.leader_telegram_id
        message = create_message("/pending", user_id=admin_id, username="admin")
        update = create_update(message=message)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await dispatcher.feed_update(bot, update)

            # Check that pending applications list was shown
            mock_answer.assert_called()
            call_text = mock_answer.call_args[0][0]
            assert "ожидающие заявки" in call_text.lower()
            assert "testplayer" in call_text.lower()


@pytest.mark.asyncio
async def test_dispatcher_middleware_and_di(dispatcher: Dispatcher, bot: MagicMock):
    """Test that dispatcher properly injects dependencies."""
    message = create_message("/start")
    update = create_update(message=message)

    with patch.object(Message, "answer", new=AsyncMock()):
        # This should not raise errors about missing dependencies
        await dispatcher.feed_update(bot, update)

    # Verify DI is configured
    assert "db" in dispatcher.workflow_data
    assert "settings" in dispatcher.workflow_data
