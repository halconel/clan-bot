"""Decorators for bot handlers."""

from functools import wraps
from typing import Callable, Union

from aiogram.types import CallbackQuery, Message

from config.settings import Settings


def admin_only(handler: Callable) -> Callable:
    """Decorator to restrict handler to admin users only.

    Works with both Message and CallbackQuery handlers.
    Automatically sends error message if user is not admin.

    Args:
        handler: Handler function to wrap

    Returns:
        Wrapped handler function

    Example:
        @router.message(Command("pending"))
        @admin_only
        async def cmd_pending(message: Message, db: Database, settings: Settings):
            # Handler code here
    """

    @wraps(handler)
    async def wrapper(event: Union[Message, CallbackQuery], *args, **kwargs):
        # Extract settings from kwargs or args
        # In aiogram DI, settings is passed as keyword argument
        # In tests, it might be passed as positional argument
        settings: Settings = kwargs.get("settings")

        if not settings and args:
            # Try to find Settings in args
            for arg in args:
                if isinstance(arg, Settings):
                    settings = arg
                    break

        if not settings:
            raise ValueError("Settings not found in handler arguments")

        # Get user_id from event
        user_id = event.from_user.id

        # Check if user is admin
        if user_id != settings.telegram.leader_telegram_id:
            error_msg = "❌ У вас нет прав для выполнения этого действия."

            if isinstance(event, CallbackQuery):
                await event.answer(error_msg, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(error_msg)

            return

        # User is admin, proceed with handler
        return await handler(event, *args, **kwargs)

    return wrapper
