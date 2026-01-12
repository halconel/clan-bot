"""Admin keyboards for player management."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_approve_reject_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with approve/reject buttons for pending registration.

    Args:
        telegram_id: Telegram ID of the pending player

    Returns:
        InlineKeyboardMarkup with approve and reject buttons
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve:{telegram_id}",
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject:{telegram_id}",
        ),
    )
    return builder.as_markup()


def get_player_management_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for player management (exclude, edit).

    Args:
        telegram_id: Telegram ID of the player

    Returns:
        InlineKeyboardMarkup with management buttons
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🚫 Отчислить",
            callback_data=f"exclude:{telegram_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить статус",
            callback_data=f"edit_status:{telegram_id}",
        ),
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard with cancel button.

    Returns:
        InlineKeyboardMarkup with cancel button
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel",
        ),
    )
    return builder.as_markup()
