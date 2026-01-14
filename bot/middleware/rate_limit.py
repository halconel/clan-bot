"""Rate limiting middleware to prevent flood attacks."""

import logging
import time
from collections import defaultdict
from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware to limit request rate per user.

    Prevents flood attacks by limiting number of commands per time window.
    Based on best practices from:
    - https://grammy.dev/advanced/flood
    - https://bazucompany.com/blog/how-to-secure-a-telegram-bot-best-practices/
    """

    def __init__(
        self,
        rate_limit: int = 5,
        time_window: int = 60,
    ):
        """
        Initialize rate limiting middleware.

        Args:
            rate_limit: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window

        # Storage: {user_id: [(timestamp1, timestamp2, ...)]}
        self.user_timestamps: dict[int, list[float]] = defaultdict(list)

    def _cleanup_old_timestamps(self, user_id: int, current_time: float) -> None:
        """Remove timestamps older than time window."""
        cutoff_time = current_time - self.time_window
        self.user_timestamps[user_id] = [
            ts for ts in self.user_timestamps[user_id] if ts > cutoff_time
        ]

    def _is_rate_limited(self, user_id: int) -> tuple[bool, int]:
        """
        Check if user exceeded rate limit.

        Returns:
            Tuple of (is_limited, seconds_until_reset)
        """
        current_time = time.time()

        # Clean up old timestamps
        self._cleanup_old_timestamps(user_id, current_time)

        timestamps = self.user_timestamps[user_id]

        if len(timestamps) >= self.rate_limit:
            # User exceeded rate limit
            oldest_timestamp = min(timestamps)
            seconds_until_reset = int(self.time_window - (current_time - oldest_timestamp)) + 1
            return True, seconds_until_reset

        return False, 0

    def _record_request(self, user_id: int) -> None:
        """Record new request timestamp for user."""
        self.user_timestamps[user_id].append(time.time())

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process incoming update with rate limiting."""
        # Only apply rate limiting to messages
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        user_id = user.id

        # Check if user is rate limited
        is_limited, seconds_until_reset = self._is_rate_limited(user_id)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for user {user_id} (@{user.username}). "
                f"Reset in {seconds_until_reset}s"
            )
            await event.answer(
                f"⏱ <b>Слишком много запросов!</b>\n\n"
                f"Пожалуйста, подождите <b>{seconds_until_reset} сек.</b> "
                f"перед следующей командой.\n\n"
                f"<i>Это необходимо для защиты бота от перегрузки.</i>"
            )
            return None

        # Record this request
        self._record_request(user_id)

        # Continue processing
        return await handler(event, data)
