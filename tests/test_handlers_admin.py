"""Integration tests for admin handlers."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Chat, Message, User

from bot.handlers.admin import (
    cmd_exclude,
    cmd_list,
    cmd_pending,
    process_approve,
    process_reject,
)
from config.settings import Settings
from database.database import Database
from database.repository import PlayerRepository
from models.player import PendingRegistration, Player

# Import helper functions from conftest
from tests.conftest import create_callback, create_message


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

        # Create callback
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=admin_chat,
            from_user=admin_user,
            caption="Test pending application",
        )
        callback = create_callback(f"approve:{pending_user_id}", admin_user, message)

        # Mock bot and message methods
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        # Use object.__setattr__ to bypass frozen model
        object.__setattr__(callback, "_bot", mock_bot)

        with (
            patch.object(CallbackQuery, "answer", new=AsyncMock()) as mock_answer,
            patch.object(Message, "edit_caption", new=AsyncMock()) as mock_edit,
        ):
            await process_approve(callback, database, test_settings)

            # Check that approval was processed
            mock_answer.assert_called_once()
            assert "одобрена" in mock_answer.call_args[0][0].lower()

            # Check that message was edited
            mock_edit.assert_called_once()

            # Check that user was notified
            mock_bot.send_message.assert_called_once()
            assert mock_bot.send_message.call_args[1]["chat_id"] == pending_user_id

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

    @pytest.mark.asyncio
    async def test_approve_by_non_admin(
        self, database: Database, test_settings: Settings, user: User, chat: Chat
    ):
        """Test that non-admin cannot approve."""
        message = create_message("", user, chat)
        callback = create_callback("approve:123456789", user, message)

        with patch.object(CallbackQuery, "answer", new=AsyncMock()) as mock_answer:
            await process_approve(callback, database, test_settings)

            # Check that rejection was sent
            mock_answer.assert_called_once()
            assert "нет прав" in mock_answer.call_args[0][0].lower()


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

        # Create callback
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=admin_chat,
            from_user=admin_user,
            caption="Test pending application",
        )
        callback = create_callback(f"reject:{pending_user_id}", admin_user, message)

        # Mock bot and message methods
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        # Use object.__setattr__ to bypass frozen model
        object.__setattr__(callback, "_bot", mock_bot)

        with (
            patch.object(CallbackQuery, "answer", new=AsyncMock()) as mock_answer,
            patch.object(Message, "edit_caption", new=AsyncMock()) as mock_edit,
        ):
            await process_reject(callback, database, test_settings)

            # Check that rejection was processed
            mock_answer.assert_called_once()
            assert "отклонена" in mock_answer.call_args[0][0].lower()

            # Check that message was edited
            mock_edit.assert_called_once()

        # Check that pending was removed
        async for session in database.get_session():
            repo = PlayerRepository(session)
            pending = await repo.get_pending(pending_user_id)
            assert pending is None


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

        message = create_message("/pending", admin_user, admin_chat)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await cmd_pending(message, database, test_settings)

            # Check that response was sent
            mock_answer.assert_called_once()
            response_text = mock_answer.call_args[0][0]
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

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await cmd_pending(message, database, test_settings)

            # Check that empty message was sent
            mock_answer.assert_called_once()
            response_text = mock_answer.call_args[0][0]
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

        message = create_message("/list", admin_user, admin_chat)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await cmd_list(message, database, test_settings)

            # Check that response was sent
            mock_answer.assert_called_once()
            response_text = mock_answer.call_args[0][0]
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

        message = create_message("/exclude @testplayer Нарушение правил", admin_user, admin_chat)

        # Mock bot methods
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        # Use object.__setattr__ to bypass frozen model
        object.__setattr__(message, "_bot", mock_bot)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await cmd_exclude(message, database, test_settings)

            # Check that success message was sent
            mock_answer.assert_called_once()
            response_text = mock_answer.call_args[0][0]
            assert "отчислен" in response_text.lower()

        # Check that player was excluded in database
        async for session in database.get_session():
            repo = PlayerRepository(session)
            player = await repo.get_player(player_id)
            assert player is not None
            assert player.status == "Отчислен"
            assert player.exclusion_reason == "Нарушение правил"

    @pytest.mark.asyncio
    async def test_exclude_invalid_format(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test exclude with invalid command format."""
        message = create_message("/exclude @testplayer", admin_user, admin_chat)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await cmd_exclude(message, database, test_settings)

            # Check that error message was sent
            mock_answer.assert_called_once()
            response_text = mock_answer.call_args[0][0]
            assert "неверный формат" in response_text.lower()

    @pytest.mark.asyncio
    async def test_exclude_non_existing_player(
        self, database: Database, test_settings: Settings, admin_user: User, admin_chat: Chat
    ):
        """Test excluding player that doesn't exist."""
        message = create_message("/exclude @nonexistent Причина", admin_user, admin_chat)

        with patch.object(Message, "answer", new=AsyncMock()) as mock_answer:
            await cmd_exclude(message, database, test_settings)

            # Check that error message was sent
            mock_answer.assert_called_once()
            response_text = mock_answer.call_args[0][0]
            assert "не найден" in response_text.lower()
