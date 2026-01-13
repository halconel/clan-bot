"""Integration tests for common handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, User

from bot.handlers.common import cmd_cancel, cmd_help, cmd_start
from bot.states.registration import RegistrationStates


class TestStartCommand:
    """Test /start command."""

    @pytest.mark.asyncio
    async def test_start_command(self, user: User, chat: Chat):
        """Test that /start sends welcome message."""
        message = MagicMock(spec=Message)
        message.from_user = user
        message.chat = chat
        message.answer = AsyncMock()

        await cmd_start(message)

        # Check that bot sent response
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "добро пожаловать" in call_text.lower()
        assert "/register" in call_text


class TestHelpCommand:
    """Test /help command."""

    @pytest.mark.asyncio
    async def test_help_command(self, user: User, chat: Chat):
        """Test that /help sends help text."""
        message = MagicMock(spec=Message)
        message.from_user = user
        message.chat = chat
        message.answer = AsyncMock()

        await cmd_help(message)

        # Check that bot sent help text
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "доступные команды" in call_text.lower()
        assert "/register" in call_text
        assert "/pending" in call_text


class TestCancelCommand:
    """Test /cancel command."""

    @pytest.mark.asyncio
    async def test_cancel_without_state(self, user: User, chat: Chat, fsm_context: FSMContext):
        """Test /cancel when no FSM state is active."""
        message = MagicMock(spec=Message)
        message.from_user = user
        message.chat = chat
        message.answer = AsyncMock()

        await cmd_cancel(message, fsm_context)

        # Check that bot sent "no active operation" message
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "нет активной операции" in call_text.lower()

    @pytest.mark.asyncio
    async def test_cancel_with_active_state(self, user: User, chat: Chat, fsm_context: FSMContext):
        """Test /cancel when FSM state is active."""
        # Set FSM state
        await fsm_context.set_state(RegistrationStates.waiting_for_nickname)

        message = MagicMock(spec=Message)
        message.from_user = user
        message.chat = chat
        message.answer = AsyncMock()

        await cmd_cancel(message, fsm_context)

        # Check that bot sent cancellation confirmation
        message.answer.assert_called_once()
        call_text = message.answer.call_args[0][0]
        assert "операция отменена" in call_text.lower()

        # Verify state was cleared
        current_state = await fsm_context.get_state()
        assert current_state is None
