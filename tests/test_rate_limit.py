"""Tests for rate limiting middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from bot.middleware.rate_limit import RateLimitMiddleware


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class."""

    def test_init_default_params(self):
        """Test middleware initialization with default parameters."""
        middleware = RateLimitMiddleware()

        assert middleware.rate_limit == 5
        assert middleware.time_window == 60
        assert isinstance(middleware.user_timestamps, dict)
        assert len(middleware.user_timestamps) == 0

    def test_init_custom_params(self):
        """Test middleware initialization with custom parameters."""
        middleware = RateLimitMiddleware(rate_limit=10, time_window=120)

        assert middleware.rate_limit == 10
        assert middleware.time_window == 120

    def test_cleanup_old_timestamps(self):
        """Test cleanup of old timestamps."""
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)

        # Add timestamps: some old, some recent
        current_time = 1000.0
        user_id = 12345

        middleware.user_timestamps[user_id] = [
            900.0,  # 100 seconds ago - should be removed
            920.0,  # 80 seconds ago - should be removed
            950.0,  # 50 seconds ago - should stay
            980.0,  # 20 seconds ago - should stay
            995.0,  # 5 seconds ago - should stay
        ]

        middleware._cleanup_old_timestamps(user_id, current_time)

        # Should keep only timestamps within 60 seconds
        assert len(middleware.user_timestamps[user_id]) == 3
        assert 900.0 not in middleware.user_timestamps[user_id]
        assert 920.0 not in middleware.user_timestamps[user_id]
        assert 950.0 in middleware.user_timestamps[user_id]
        assert 980.0 in middleware.user_timestamps[user_id]
        assert 995.0 in middleware.user_timestamps[user_id]

    @patch("bot.middleware.rate_limit.time.time")
    def test_is_rate_limited_below_limit(self, mock_time):
        """Test rate limiting when user is below limit."""
        mock_time.return_value = 1000.0
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)
        user_id = 12345

        # Add 3 recent timestamps (below limit of 5)
        middleware.user_timestamps[user_id] = [990.0, 995.0, 998.0]

        is_limited, seconds = middleware._is_rate_limited(user_id)

        assert is_limited is False
        assert seconds == 0

    @patch("bot.middleware.rate_limit.time.time")
    def test_is_rate_limited_at_limit(self, mock_time):
        """Test rate limiting when user is at limit."""
        mock_time.return_value = 1000.0
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)
        user_id = 12345

        # Add exactly 5 timestamps (at limit)
        middleware.user_timestamps[user_id] = [950.0, 970.0, 980.0, 990.0, 995.0]

        is_limited, seconds = middleware._is_rate_limited(user_id)

        assert is_limited is True
        assert seconds > 0
        # Oldest timestamp is 950.0, so reset should be in 60 - (1000 - 950) = 10 seconds
        assert seconds == 11  # +1 for rounding

    @patch("bot.middleware.rate_limit.time.time")
    def test_is_rate_limited_cleanup_works(self, mock_time):
        """Test that cleanup happens during rate limit check."""
        mock_time.return_value = 1000.0
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)
        user_id = 12345

        # Add 6 timestamps, but 2 are old (should be cleaned up)
        middleware.user_timestamps[user_id] = [
            900.0,  # Old - should be removed
            920.0,  # Old - should be removed
            950.0,
            970.0,
            980.0,
            990.0,
        ]

        is_limited, seconds = middleware._is_rate_limited(user_id)

        # After cleanup, only 4 recent timestamps remain (below limit)
        assert is_limited is False
        assert seconds == 0
        assert len(middleware.user_timestamps[user_id]) == 4

    @patch("bot.middleware.rate_limit.time.time")
    def test_record_request(self, mock_time):
        """Test recording new request timestamp."""
        mock_time.return_value = 1000.0
        middleware = RateLimitMiddleware()
        user_id = 12345

        # Record first request
        middleware._record_request(user_id)
        assert len(middleware.user_timestamps[user_id]) == 1
        assert middleware.user_timestamps[user_id][0] == 1000.0

        # Record second request
        mock_time.return_value = 1005.0
        middleware._record_request(user_id)
        assert len(middleware.user_timestamps[user_id]) == 2
        assert middleware.user_timestamps[user_id][1] == 1005.0

    @pytest.mark.asyncio
    async def test_call_non_message_event(self):
        """Test that non-Message events are passed through."""
        middleware = RateLimitMiddleware()

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Mock non-Message event (e.g., CallbackQuery)
        event = MagicMock()
        event.__class__.__name__ = "CallbackQuery"

        data = {}

        # Should pass through without rate limiting
        result = await middleware(handler, event, data)

        assert result == "handler_result"
        handler.assert_called_once_with(event, data)

    @pytest.mark.asyncio
    async def test_call_message_without_user(self):
        """Test that messages without user are passed through."""
        middleware = RateLimitMiddleware()

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Mock Message without from_user
        message = MagicMock(spec=Message)
        message.from_user = None

        data = {}

        # Should pass through without rate limiting
        result = await middleware(handler, message, data)

        assert result == "handler_result"
        handler.assert_called_once_with(message, data)

    @pytest.mark.asyncio
    @patch("bot.middleware.rate_limit.time.time")
    async def test_call_below_rate_limit(self, mock_time):
        """Test message processing when below rate limit."""
        mock_time.return_value = 1000.0
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Mock Message with User
        user = MagicMock(spec=User)
        user.id = 12345
        user.username = "testuser"

        message = MagicMock(spec=Message)
        message.from_user = user

        data = {}

        # First request - should pass
        result = await middleware(handler, message, data)

        assert result == "handler_result"
        handler.assert_called_once_with(message, data)
        assert len(middleware.user_timestamps[12345]) == 1

    @pytest.mark.asyncio
    @patch("bot.middleware.rate_limit.time.time")
    async def test_call_exceeds_rate_limit(self, mock_time):
        """Test message blocking when rate limit exceeded."""
        mock_time.return_value = 1000.0
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Mock Message with User
        user = MagicMock(spec=User)
        user.id = 12345
        user.username = "testuser"

        message = MagicMock(spec=Message)
        message.from_user = user
        message.answer = AsyncMock()

        data = {}

        # Add 5 timestamps (at limit)
        middleware.user_timestamps[12345] = [950.0, 970.0, 980.0, 990.0, 995.0]

        # This request should be blocked
        result = await middleware(handler, message, data)

        assert result is None
        handler.assert_not_called()
        message.answer.assert_called_once()

        # Check error message contains expected text
        call_args = message.answer.call_args[0][0]
        assert "Слишком много запросов" in call_args
        assert "сек." in call_args

    @pytest.mark.asyncio
    @patch("bot.middleware.rate_limit.time.time")
    async def test_call_multiple_users_independent(self, mock_time):
        """Test that rate limiting is independent per user."""
        mock_time.return_value = 1000.0
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # User 1 - at limit
        user1 = MagicMock(spec=User)
        user1.id = 11111
        user1.username = "user1"

        message1 = MagicMock(spec=Message)
        message1.from_user = user1
        message1.answer = AsyncMock()

        # User 2 - below limit
        user2 = MagicMock(spec=User)
        user2.id = 22222
        user2.username = "user2"

        message2 = MagicMock(spec=Message)
        message2.from_user = user2

        data = {}

        # Set user1 at limit
        middleware.user_timestamps[11111] = [950.0, 970.0, 980.0, 990.0, 995.0]

        # User1 should be blocked
        result1 = await middleware(handler, message1, data)
        assert result1 is None
        message1.answer.assert_called_once()

        # User2 should pass
        handler.reset_mock()
        result2 = await middleware(handler, message2, data)
        assert result2 == "handler_result"
        handler.assert_called_once_with(message2, data)

    @pytest.mark.asyncio
    @patch("bot.middleware.rate_limit.time.time")
    async def test_call_rate_limit_resets_after_time_window(self, mock_time):
        """Test that rate limit resets after time window passes."""
        middleware = RateLimitMiddleware(rate_limit=5, time_window=60)

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Mock Message with User
        user = MagicMock(spec=User)
        user.id = 12345
        user.username = "testuser"

        message = MagicMock(spec=Message)
        message.from_user = user
        message.answer = AsyncMock()

        data = {}

        # Initial time: 1000.0
        mock_time.return_value = 1000.0

        # Add 5 old timestamps (more than 60 seconds old)
        middleware.user_timestamps[12345] = [900.0, 910.0, 920.0, 930.0, 940.0]

        # Should pass because old timestamps will be cleaned up
        result = await middleware(handler, message, data)

        assert result == "handler_result"
        handler.assert_called_once()
        # All old timestamps should be removed, new one added
        assert len(middleware.user_timestamps[12345]) == 1
        assert middleware.user_timestamps[12345][0] == 1000.0
