"""Integration tests for registration handlers."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, PhotoSize, User

from bot.handlers.registration import (
    cmd_register,
    invalid_screenshot,
    process_nickname,
    process_screenshot,
)
from bot.states.registration import RegistrationStates
from config.settings import Settings
from database.database import Database
from database.repository import PlayerRepository

# Import helper functions from conftest
from tests.conftest import create_message


class TestRegisterCommand:
    """Test /register command."""

    @pytest.mark.asyncio
    async def test_register_new_user(
        self, database: Database, test_settings: Settings, fsm_context: FSMContext, user: User, chat: Chat
    ):
        """Test registration of a new user."""
        message = create_message("/register", user, chat)

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await cmd_register(message, fsm_context, database)

            # Check that bot sent response
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
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

        message = create_message("/register", user, chat)

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await cmd_register(message, fsm_context, database)

            # Check that bot sent rejection message
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
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

        message = create_message("/register", user, chat)

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await cmd_register(message, fsm_context, database)

            # Check that bot sent rejection message
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
            assert "заявка уже отправлена" in call_text.lower()


class TestNicknameProcess:
    """Test nickname processing."""

    @pytest.mark.asyncio
    async def test_valid_nickname(self, fsm_context: FSMContext, user: User, chat: Chat):
        """Test processing valid nickname."""
        await fsm_context.set_state(RegistrationStates.waiting_for_nickname)

        message = create_message("TestPlayer", user, chat)

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await process_nickname(message, fsm_context)

            # Check that bot requested screenshot
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
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

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await process_nickname(message, fsm_context)

            # Check that bot sent error message
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
            assert "слишком короткий" in call_text.lower()

        # Check FSM state did not change
        state = await fsm_context.get_state()
        assert state == RegistrationStates.waiting_for_nickname

    @pytest.mark.asyncio
    async def test_invalid_nickname_special_chars(self, fsm_context: FSMContext, user: User, chat: Chat):
        """Test processing nickname with invalid characters."""
        await fsm_context.set_state(RegistrationStates.waiting_for_nickname)

        message = create_message("Test@Player!", user, chat)

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await process_nickname(message, fsm_context)

            # Check that bot sent error message
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
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
        message = create_message("", user, chat, photo=[photo])

        # Mock file download
        mock_file = MagicMock()
        mock_file.file_path = "photos/test.jpg"
        mock_bot = MagicMock()
        mock_bot.get_file = AsyncMock(return_value=mock_file)
        mock_bot.download_file = AsyncMock(return_value=b"fake_image_data")
        mock_bot.send_photo = AsyncMock()
        # Use object.__setattr__ to bypass frozen model
        object.__setattr__(message, '_bot', mock_bot)

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await process_screenshot(message, fsm_context, database, test_settings)

            # Check that screenshot was downloaded
            mock_bot.get_file.assert_called_once_with(photo.file_id)
            mock_bot.download_file.assert_called_once()

            # Check that confirmation was sent
            mock_answer.assert_called()

            # Check that notification was sent to admin
            mock_bot.send_photo.assert_called_once()

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

    @pytest.mark.asyncio
    async def test_no_photo_sent(self, fsm_context: FSMContext, user: User, chat: Chat):
        """Test when user sends message without photo."""
        await fsm_context.set_state(RegistrationStates.waiting_for_screenshot)

        message = create_message("Some text", user, chat)

        with patch.object(Message, 'answer', new=AsyncMock()) as mock_answer:
            await invalid_screenshot(message)

            # Check that bot sent error message
            mock_answer.assert_called_once()
            call_text = mock_answer.call_args[0][0]
            assert "отправьте" in call_text.lower() and "фотографию" in call_text.lower()

        # Check FSM state did not change (should remain in waiting_for_screenshot)
        state = await fsm_context.get_state()
        assert state == RegistrationStates.waiting_for_screenshot
